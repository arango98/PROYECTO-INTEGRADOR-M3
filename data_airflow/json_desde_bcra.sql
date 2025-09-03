CREATE OR REPLACE EXTERNAL TABLE `eng-name-468100-g3.raw_data.bcra_exchange_rates`
(
  fecha STRING,
  moneda STRING,
  descripcion STRING,
  valor_venta FLOAT64
)
OPTIONS (
  format = 'JSON', 
  uris = ['gs://bucket-pi-m3-anhs/raw/*']
);