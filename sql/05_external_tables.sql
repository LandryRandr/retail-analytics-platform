
/* ------------------------------------
        PRODUCTS - EXTERNAL TABLE 
        ---------------------------------*/
CREATE EXTERNAL TABLE RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_PRODUCTS (
    product_id NUMBER(3,0) AS (VALUE:c1::NUMBER(3,0)),
    product_name TEXT AS (VALUE:c2::TEXT),
    category TEXT AS (VALUE:c3::TEXT),
    unit_price NUMBER(6,2) AS (VALUE:c4::NUMBER(6,2))
)
WITH LOCATION = @RETAIL_ANALYTICS.RAW_EXT.RETAIL_ANALYTICS_RAW_STAGE/products/
FILE_FORMAT = RETAIL_ANALYTICS.RAW_EXT.CSV_FORMAT
AUTO_REFRESH = FALSE;


ALTER EXTERNAL TABLE RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_PRODUCTS
REFRESH;

SELECT *
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_PRODUCTS
LIMIT 10;



/* ------------------------------------
        ORDERS - EXTERNAL STORAGE  
    ----------------------------------- */
SELECT *
FROM TABLE(
    INFER_SCHEMA(
        LOCATION => '@RETAIL_ANALYTICS.RAW_EXT.RETAIL_ANALYTICS_RAW_STAGE/orders/',
        FILE_FORMAT => 'RETAIL_ANALYTICS.RAW_EXT.CSV_FORMAT'
    )
);

CREATE OR REPLACE EXTERNAL TABLE RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDERS (
    order_id NUMBER(3,0) AS (VALUE:c1::NUMBER(3,0)),
    customer_id NUMBER(3,0) AS (VALUE:c2::NUMBER(3,0)),
    order_date DATE AS (VALUE:c3::DATE),

    year NUMBER AS (
        SPLIT_PART(
            SPLIT_PART(METADATA$FILENAME, 'year=', 2),
            '/',
            1
        )::NUMBER
    ),

    quarter TEXT AS (
        SPLIT_PART(
            SPLIT_PART(METADATA$FILENAME, 'quarter=', 2),
            '/',
            1
        )
    )
)
WITH LOCATION = @RETAIL_ANALYTICS.RAW_EXT.RETAIL_ANALYTICS_RAW_STAGE/orders/
FILE_FORMAT = RETAIL_ANALYTICS.RAW_EXT.CSV_FORMAT
AUTO_REFRESH = FALSE;


ALTER EXTERNAL TABLE RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDERS
REFRESH;


SELECT
    order_id,
    customer_id,
    order_date,
    year,
    quarter
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDERS
LIMIT 10;


select 
    year,
    quarter,
    count(*) as ORDER_COUNT
from retail_analytics.raw_ext.external_orders
group by year, quarter
order by year, quarter;