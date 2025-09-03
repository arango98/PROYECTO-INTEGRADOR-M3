    DROP SCHEMA IF EXISTS `eng-name-468100-g3.raw_data` CASCADE;
    DROP SCHEMA IF EXISTS `eng-name-468100-g3.transformed_data` CASCADE;
    DROP SCHEMA IF EXISTS `eng-name-468100-g3.business_layer` CASCADE;
    CREATE SCHEMA `eng-name-468100-g3.raw_data`
    OPTIONS(
      location = 'US'
    );

    CREATE SCHEMA `eng-name-468100-g3.transformed_data`
    OPTIONS(
      location = 'US'
    );

    CREATE SCHEMA `eng-name-468100-g3.business_layer`
    OPTIONS(
      location = 'US'
    );