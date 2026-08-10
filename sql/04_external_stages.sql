/* 2. STORAGE INTEGRATION */

CREATE OR REPLACE STORAGE INTEGRATION RETAIL_ANALYTICS_S3_INT
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = S3
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::218712444577:role/Retail_analytics_Snowflake_role'
    STORAGE_ALLOWED_LOCATIONS = (
        's3://retail-analytics-s3-218712444577/raw/'
    );

/* 3. To get the STORAGE_AWS_IAM_USER_ARN and the STORAGE_AWS_EXTERNAL_ID */
DESC STORAGE INTEGRATION RETAIL_ANALYTICS_S3_INT;


/* 4. 
Create the role + policy + Trust relationships in AWS
_ Policy :
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListRawBucket",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::retail-analytics-s3-218712444577"
        },
        {
            "Sid": "ReadRawData",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::retail-analytics-s3-218712444577/raw/*"
        }
    ]
}

_Trust relationship (json):
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "SnowflakeAssumeRole",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::334575333482:user/grvx1000-s"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "PS15128_SFCRole=3_0xnVh72idI/q2OKTZ1EppLX0mNc="
                }
            }
        }
    ]
}
End */


/* 5. Snowflake need to validate the AWS configuration */

SELECT SYSTEM$VALIDATE_STORAGE_INTEGRATION(
    'RETAIL_ANALYTICS_S3_INT',
    's3://retail-analytics-s3-218712444577/raw/',
    'products/products.csv',
    'read'
);




/*  ---------------------
    EXTERNAL STAGE
    ---------------------*/
CREATE OR REPLACE STAGE RETAIL_ANALYTICS_RAW_STAGE
    URL = 's3://retail-analytics-s3-218712444577/raw/'
    STORAGE_INTEGRATION = RETAIL_ANALYTICS_S3_INT;

SHOW STAGES;

LIST @RETAIL_ANALYTICS_RAW_STAGE;






SHOW FILE FORMATS IN DATABASE RETAIL_ANALYTICS;

--SCHEMA DISCOVERY -- INFER_SCHEMA DETEMINES TYPE
SELECT *
FROM TABLE(
    INFER_SCHEMA(
        LOCATION => '@RETAIL_ANALYTICS.RAW_EXT.RETAIL_ANALYTICS_RAW_STAGE/products/',
        FILE_FORMAT => 'RETAIL_ANALYTICS.RAW_EXT.CSV_FORMAT'
    )
);


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