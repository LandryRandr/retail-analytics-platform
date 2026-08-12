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


LIST @RETAIL_ANALYTICS.RAW_EXT.RETAIL_ANALYTICS_RAW_STAGES;