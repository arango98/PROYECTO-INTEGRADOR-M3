--AVANCE 3

CREATE OR REPLACE TABLE `eng-name-468100-g3.transformed_data.listings_cleaned` AS
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
    `eng-name-468100-g3.raw_data.ab_nyc`
  WHERE
    price > 0 
),


Latest_Exchange_Rate AS (
  SELECT
    valor_venta
  FROM
    `eng-name-468100-g3.raw_data.bcra_exchange_rates`

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

CREATE OR REPLACE TABLE `eng-name-468100-g3.business_layer.avg_price_by_neighbourhood` AS
SELECT
  neighbourhood_group,
  neighbourhood,
  COUNT(listing_id) AS total_listings,
  AVG(price_usd) AS avg_price_usd,
  AVG(price_ars) AS avg_price_ars
FROM
  `eng-name-468100-g3.transformed_data.listings_cleaned`
GROUP BY
  neighbourhood_group,
  neighbourhood
ORDER BY
  avg_price_usd DESC;


CREATE OR REPLACE TABLE `eng-name-468100-g3.business_layer.room_type_analysis` AS
SELECT
  room_type,
  COUNT(listing_id) AS total_listings,
  SUM(price_usd * (365 - availability_365)) AS estimated_revenue_usd,
  SUM(price_ars * (365 - availability_365)) AS estimated_revenue_ars
FROM
  `eng-name-468100-g3.transformed_data.listings_cleaned`
WHERE 
  availability_365 < 365
GROUP BY
  room_type
ORDER BY
  total_listings DESC;


CREATE OR REPLACE TABLE `eng-name-468100-g3.business_layer.top_hosts_analysis` AS
SELECT
  host_id,
  host_name,
  SUM(host_listings_count) AS total_listings,
  AVG(price_usd) AS avg_price_usd,
  MIN(price_usd) AS min_price_usd,
  MAX(price_usd) AS max_price_usd
FROM
  `eng-name-468100-g3.transformed_data.listings_cleaned`
GROUP BY
  host_id,
  host_name
ORDER BY
  total_listings DESC
LIMIT 20;

CREATE OR REPLACE TABLE `eng-name-468100-g3.business_layer.reviews_evolution_by_month` AS
SELECT
  neighbourhood_group,
  EXTRACT(YEAR FROM last_review) AS review_year,
  EXTRACT(MONTH FROM last_review) AS review_month,
  COUNT(listing_id) AS total_reviews
FROM
  `eng-name-468100-g3.transformed_data.listings_cleaned`
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
