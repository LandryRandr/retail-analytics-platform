/*  ACTIVER LE AFRICA CAP TOWN REGION AVANT DE FAIRE QUOI QUE CE SOIT EN AFRIQUE  */


/* 1. STORAGE INTEGRATION POLICY

json :
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:DeleteObject",
                "s3:DeleteObjectVersion"
            ],
            "Resource": "arn:aws:s3:::retail-analytics-s3-218712444577/raw/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::retail-analytics-s3-218712444577",
            "Condition": {
                "StringLike": {
                    "s3:prefix": [
                        "raw/*"
                    ]
                }
            }
        }
    ]
}

*/


/* 2. IAM role creation + policy */


/* 3. STORAGE INTEGRATION */
CREATE STORAGE INTEGRATION RETAIL_ANALYTICS_S3_INT
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::218712444577:role/Snowflake_data_integration_role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://retail-analytics-s3-218712444577/raw/') ;


/* 4. get the STORAGE_AWS_IAM_USER_ARN and the STORAGE_AWS_EXTERNAL_ID */
DESC INTEGRATION RETAIL_ANALYTICS_S3_INT;


/* 5. Finalize the Trust relationships in AWS
json :

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::574644335091:user/zz342000-s"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "IC63985_SFCRole=6_ZNXhkM6zdxPG5ezf62uVPdKE9LI="
                }
            }
        }
    ]
}
End */



SELECT CURRENT_ACCOUNT(),
       CURRENT_REGION(),
       CURRENT_ROLE(),
       CURRENT_USER();





/* 6. Snowflake need to validate the AWS configuration */

SELECT SYSTEM$VALIDATE_STORAGE_INTEGRATION(
    'RETAIL_ANALYTICS_S3_INT',
    's3://retail-analytics-s3-218712444577/raw/',
    'products/products.csv',
    'read'
);





/*  ---------------------
    7. EXTERNAL STAGE
    ---------------------*/
CREATE OR REPLACE STAGE RETAIL_ANALYTICS.RAW_EXT.RETAIL_ANALYTICS_RAW_STAGE
    URL = 's3://retail-analytics-s3-218712444577/raw/'
    STORAGE_INTEGRATION = RETAIL_ANALYTICS_S3_INT;

SHOW STAGES;



LIST @RETAIL_ANALYTICS.RAW_EXT.RETAIL_ANALYTICS_RAW_STAGE;


SHOW FILE FORMATS IN DATABASE RETAIL_ANALYTICS;

--SCHEMA DISCOVERY -- INFER_SCHEMA DETEMINES TYPE
SELECT *
FROM TABLE(
    INFER_SCHEMA(
        LOCATION => '@RETAIL_ANALYTICS.RAW_EXT.RETAIL_ANALYTICS_RAW_STAGE/products/',
        FILE_FORMAT => 'RETAIL_ANALYTICS.RAW_EXT.CSV_FORMAT'
    )
);

