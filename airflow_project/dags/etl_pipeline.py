from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryExecuteQueryOperator

GCP_PROJECT_ID = "eng-name-468100-g3"
BIGQUERY_RAW_DATASET = "raw_data" 
BIGQUERY_TRANSFORMED_DATASET = "transformed_data"
BIGQUERY_BUSINESS_DATASET = "business_layer"

TRANSFORMATION_SQL = f"""
-- PASO 1: Crear la tabla limpia y enriquecida en la capa transformada
CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BIGQUERY_TRANSFORMED_DATASET}.listings_cleaned` AS
WITH Staging_Listings AS (
  SELECT
    id AS listing_id,
    name,
    host_id,
    host_name,
    neighbourhood_group,
    neighbourhood,
    latitude,
    longitude,
    room_type,
    SAFE_CAST(price AS FLOAT64) AS price_usd,
    SAFE_CAST(minimum_nights AS INT64) AS minimum_nights,
    SAFE_CAST(number_of_reviews AS INT64) AS number_of_reviews,
    SAFE_CAST(last_review AS DATE) AS last_review,
    COALESCE(SAFE_CAST(reviews_per_month AS FLOAT64), 0) AS reviews_per_month,
    SAFE_CAST(calculated_host_listings_count AS INT64) AS host_listings_count,
    SAFE_CAST(availability_365 AS INT64) AS availability_365
  FROM
    `{GCP_PROJECT_ID}.{BIGQUERY_RAW_DATASET}.ab_nyc`
  WHERE
    SAFE_CAST(price AS FLOAT64) > 0
),
Latest_Exchange_Rate AS (
  SELECT
    valor_venta
  FROM
    `{GCP_PROJECT_ID}.{BIGQUERY_RAW_DATASET}.bcra_exchange_rates`
  QUALIFY ROW_NUMBER() OVER(ORDER BY fecha DESC) = 1
)
SELECT
  listings.*,
  exchange.valor_venta AS usd_to_ars_rate,
  (listings.price_usd * exchange.valor_venta) AS price_ars
FROM
  Staging_Listings AS listings
CROSS JOIN
  Latest_Exchange_Rate AS exchange;

-- PASO 2.1: Crear tabla de precio promedio por barrio
CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BIGQUERY_BUSINESS_DATASET}.avg_price_by_neighbourhood` AS
SELECT
  neighbourhood_group,
  neighbourhood,
  COUNT(listing_id) AS total_listings,
  AVG(price_usd) AS avg_price_usd,
  AVG(price_ars) AS avg_price_ars
FROM
  `{GCP_PROJECT_ID}.{BIGQUERY_TRANSFORMED_DATASET}.listings_cleaned`
GROUP BY
  neighbourhood_group,
  neighbourhood
ORDER BY
  avg_price_usd DESC;

-- PASO 2.2: Crear tabla de análisis por tipo de habitación
CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BIGQUERY_BUSINESS_DATASET}.room_type_analysis` AS
SELECT
  room_type,
  COUNT(listing_id) AS total_listings,
  SUM(price_usd * (365 - availability_365)) AS estimated_revenue_usd,
  SUM(price_ars * (365 - availability_365)) AS estimated_revenue_ars
FROM
  `{GCP_PROJECT_ID}.{BIGQUERY_TRANSFORMED_DATASET}.listings_cleaned`
WHERE 
  availability_365 < 365
GROUP BY
  room_type
ORDER BY
  total_listings DESC;

-- PASO 2.3: Crear tabla de análisis de top hosts
CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BIGQUERY_BUSINESS_DATASET}.top_hosts_analysis` AS
SELECT
  host_id,
  host_name,
  SUM(host_listings_count) AS total_listings,
  AVG(price_usd) AS avg_price_usd,
  MIN(price_usd) AS min_price_usd,
  MAX(price_usd) AS max_price_usd
FROM
  `{GCP_PROJECT_ID}.{BIGQUERY_TRANSFORMED_DATASET}.listings_cleaned`
GROUP BY
  host_id,
  host_name
ORDER BY
  total_listings DESC
LIMIT 20;

-- PASO 2.4: Crear tabla de evolución de reseñas
CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BIGQUERY_BUSINESS_DATASET}.reviews_evolution_by_month` AS
SELECT
  neighbourhood_group,
  EXTRACT(YEAR FROM last_review) AS review_year,
  EXTRACT(MONTH FROM last_review) AS review_month,
  COUNT(listing_id) AS total_reviews
FROM
  `{GCP_PROJECT_ID}.{BIGQUERY_TRANSFORMED_DATASET}.listings_cleaned`
WHERE
  last_review IS NOT NULL
GROUP BY
  neighbourhood_group,
  review_year,
  review_month
ORDER BY
  review_year,
  review_month,
  neighbourhood_group;
"""

with DAG(
    dag_id="elt_bigquery_pipeline",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    schedule="@daily",
    tags=["elt", "bigquery"],
) as dag:
    transform_and_load_to_business_layer = BigQueryExecuteQueryOperator(
        task_id="transform_and_load_to_business_layer",
        sql=TRANSFORMATION_SQL,
        use_legacy_sql=False,
        gcp_conn_id="google_cloud_default",
    )
