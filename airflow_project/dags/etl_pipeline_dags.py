from __future__ import annotations

import pendulum

from airflow.models import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryExecuteQueryOperator
# Importamos la clase Mount para definir volúmenes correctamente
from docker.types import Mount

# --- Constantes y Configuración ---
GCP_PROJECT_ID = "eng-name-468100-g3"
BIGQUERY_RAW_DATASET = "raw_data"
BIGQUERY_TRANSFORMED_DATASET = "transformed_data"
BIGQUERY_BUSINESS_DATASET = "business_layer"
# Ruta a las credenciales DENTRO del contenedor de Airflow (la ruta final y corregida)
GCP_CREDENTIALS_FILE = "/usr/local/share/credentials/gcp_credentials.json"

# Script SQL completo para la transformación
TRANSFORMATION_SQL = f"""
-- PASO 1: Crear la tabla limpia y enriquecida en la capa transformada
CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BIGQUERY_TRANSFORMED_DATASET}.listings_cleaned` AS
WITH Staging_Listings AS (
  SELECT
    id AS listing_id, name, host_id, host_name, neighbourhood_group, neighbourhood,
    latitude, longitude, room_type,
    SAFE_CAST(price AS FLOAT64) AS price_usd,
    SAFE_CAST(minimum_nights AS INT64) AS minimum_nights,
    SAFE_CAST(number_of_reviews AS INT64) AS number_of_reviews,
    SAFE_CAST(last_review AS DATE) AS last_review,
    COALESCE(SAFE_CAST(reviews_per_month AS FLOAT64), 0) AS reviews_per_month,
    SAFE_CAST(calculated_host_listings_count AS INT64) AS host_listings_count,
    SAFE_CAST(availability_365 AS INT64) AS availability_365
  FROM `{GCP_PROJECT_ID}.{BIGQUERY_RAW_DATASET}.ab_nyc`
  WHERE SAFE_CAST(price AS FLOAT64) > 0
),
Latest_Exchange_Rate AS (
  SELECT valor_venta
  FROM `{GCP_PROJECT_ID}.{BIGQUERY_RAW_DATASET}.bcra_exchange_rates`
  QUALIFY ROW_NUMBER() OVER(ORDER BY fecha DESC) = 1
)
SELECT
  listings.*,
  exchange.valor_venta AS usd_to_ars_rate,
  (listings.price_usd * exchange.valor_venta) AS price_ars
FROM Staging_Listings AS listings
CROSS JOIN Latest_Exchange_Rate AS exchange;

-- PASO 2.1: Crear tabla de precio promedio por barrio
CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BIGQUERY_BUSINESS_DATASET}.avg_price_by_neighbourhood` AS
SELECT
  neighbourhood_group, neighbourhood, COUNT(listing_id) AS total_listings,
  AVG(price_usd) AS avg_price_usd, AVG(price_ars) AS avg_price_ars
FROM `{GCP_PROJECT_ID}.{BIGQUERY_TRANSFORMED_DATASET}.listings_cleaned`
GROUP BY neighbourhood_group, neighbourhood
ORDER BY avg_price_usd DESC;

-- PASO 2.2: Crear tabla de análisis por tipo de habitación
CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BIGQUERY_BUSINESS_DATASET}.room_type_analysis` AS
SELECT
  room_type, COUNT(listing_id) AS total_listings,
  SUM(price_usd * (365 - availability_365)) AS estimated_revenue_usd,
  SUM(price_ars * (365 - availability_365)) AS estimated_revenue_ars
FROM `{GCP_PROJECT_ID}.{BIGQUERY_TRANSFORMED_DATASET}.listings_cleaned`
WHERE availability_365 < 365
GROUP BY room_type
ORDER BY total_listings DESC;
"""

with DAG(
    dag_id="full_elt_pipeline",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    schedule="@daily",
    tags=["elt", "docker", "bigquery"],
) as dag:
    # --- Tarea 1: Extracción (Ejecutar nuestro contenedor Docker) ---
    extract_task = DockerOperator(
        task_id="run_bcra_extractor",
        image="anhsoria/bcra-extractor:1.0",
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        # Usamos la clase Mount para definir el volumen correctamente
        mounts=[
            Mount(
                source=GCP_CREDENTIALS_FILE,
                target="/app/gcp_credentials.json",
                type="bind",
                read_only=True
            )
        ],
        auto_remove=True,
    )

    # --- Tarea 2: Transformación (Ejecutar SQL en BigQuery) ---
    transform_task = BigQueryExecuteQueryOperator(
        task_id="run_bigquery_transformations",
        sql=TRANSFORMATION_SQL,
        use_legacy_sql=False,
        gcp_conn_id="google_cloud_default",
    )

    # --- Definición de Dependencias ---
    extract_task >> transform_task