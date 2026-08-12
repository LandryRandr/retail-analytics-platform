
-- CHECK EXTERNAL TABLES
SELECT
    'CUSTOMERS' AS SOURCE,
    COUNT(*) AS ROW_COUNT
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_CUSTOMERS

UNION ALL

SELECT
    'PRODUCTS',
    COUNT(*)
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_PRODUCTS

UNION ALL

SELECT
    'ORDERS',
    COUNT(*)
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDERS

UNION ALL

SELECT
    'ORDER_ITEMS',
    COUNT(*)
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDER_ITEMS;



/* ====
        AUTOMATION
                   ==== */

USE DATABASE RETAIL_ANALYTICS;
USE SCHEMA SILVER;

CREATE OR REPLACE PROCEDURE PROCESS_NEW_SILVER_FILES()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_result VARCHAR DEFAULT '';
BEGIN

    /* =========================================================
       1. CUSTOMERS
       ========================================================= */

    INSERT INTO RETAIL_ANALYTICS.SILVER.CUSTOMERS (
        customer_id,
        first_name,
        last_name,
        email,
        city,
        country,
        signup_date
    )
    SELECT
        e.customer_id,
        e.first_name,
        e.last_name,
        e.email,
        e.city,
        e.country,
        e.signup_date
    FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_CUSTOMERS e
    WHERE NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG l
        WHERE l.SOURCE_FILE = e.METADATA$FILENAME
          AND l.TARGET_TABLE = 'CUSTOMERS'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.CUSTOMERS s
        WHERE s.customer_id = e.customer_id
    );


    /* Log customer files */

    INSERT INTO RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
        SOURCE_FILE,
        TARGET_TABLE
    )
    SELECT DISTINCT
        e.METADATA$FILENAME,
        'CUSTOMERS'
    FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_CUSTOMERS e
    WHERE NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG l
        WHERE l.SOURCE_FILE = e.METADATA$FILENAME
          AND l.TARGET_TABLE = 'CUSTOMERS'
    );


    /* =========================================================
       2. PRODUCTS
       ========================================================= */

    INSERT INTO RETAIL_ANALYTICS.SILVER.PRODUCTS (
        product_id,
        product_name,
        category,
        unit_price
    )
    SELECT
        e.product_id,
        e.product_name,
        e.category,
        e.unit_price
    FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_PRODUCTS e
    WHERE NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG l
        WHERE l.SOURCE_FILE = e.METADATA$FILENAME
          AND l.TARGET_TABLE = 'PRODUCTS'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.PRODUCTS s
        WHERE s.product_id = e.product_id
    );


    /* Log product files */

    INSERT INTO RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
        SOURCE_FILE,
        TARGET_TABLE
    )
    SELECT DISTINCT
        e.METADATA$FILENAME,
        'PRODUCTS'
    FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_PRODUCTS e
    WHERE NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG l
        WHERE l.SOURCE_FILE = e.METADATA$FILENAME
          AND l.TARGET_TABLE = 'PRODUCTS'
    );


    /* =========================================================
       3. ORDERS
       ========================================================= */

    INSERT INTO RETAIL_ANALYTICS.SILVER.ORDERS (
        order_id,
        customer_id,
        order_date,
        year,
        quarter
    )
    SELECT
        e.order_id,
        e.customer_id,
        e.order_date,
        e.year,
        e.quarter
    FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDERS e
    WHERE NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG l
        WHERE l.SOURCE_FILE = e.METADATA$FILENAME
          AND l.TARGET_TABLE = 'ORDERS'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.ORDERS s
        WHERE s.order_id = e.order_id
    );


    /* Log order files */

    INSERT INTO RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
        SOURCE_FILE,
        TARGET_TABLE
    )
    SELECT DISTINCT
        e.METADATA$FILENAME,
        'ORDERS'
    FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDERS e
    WHERE NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG l
        WHERE l.SOURCE_FILE = e.METADATA$FILENAME
          AND l.TARGET_TABLE = 'ORDERS'
    );


    /* =========================================================
       4. ORDER ITEMS
       ========================================================= */

    INSERT INTO RETAIL_ANALYTICS.SILVER.ORDER_ITEMS (
        order_id,
        product_id,
        quantity,
        unit_price,
        year,
        quarter
    )
    SELECT
        e.order_id,
        e.product_id,
        e.quantity,
        e.unit_price,
        e.year,
        e.quarter
    FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDER_ITEMS e
    WHERE NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG l
        WHERE l.SOURCE_FILE = e.METADATA$FILENAME
          AND l.TARGET_TABLE = 'ORDER_ITEMS'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.ORDER_ITEMS s
        WHERE s.order_id = e.order_id
          AND s.product_id = e.product_id
    );


    /* Log order-item files */

    INSERT INTO RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
        SOURCE_FILE,
        TARGET_TABLE
    )
    SELECT DISTINCT
        e.METADATA$FILENAME,
        'ORDER_ITEMS'
    FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDER_ITEMS e
    WHERE NOT EXISTS (
        SELECT 1
        FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG l
        WHERE l.SOURCE_FILE = e.METADATA$FILENAME
          AND l.TARGET_TABLE = 'ORDER_ITEMS'
    );


    RETURN 'Silver ingestion completed successfully';

END;
$$;


-- MANUALLY EXECUTE
CALL RETAIL_ANALYTICS.SILVER.PROCESS_NEW_SILVER_FILES();


SELECT 'CUSTOMERS' AS TABLE_NAME, COUNT(*) AS ROW_COUNT
FROM RETAIL_ANALYTICS.SILVER.CUSTOMERS

UNION ALL

SELECT 'PRODUCTS', COUNT(*)
FROM RETAIL_ANALYTICS.SILVER.PRODUCTS

UNION ALL

SELECT 'ORDERS', COUNT(*)
FROM RETAIL_ANALYTICS.SILVER.ORDERS

UNION ALL

SELECT 'ORDER_ITEMS', COUNT(*)
FROM RETAIL_ANALYTICS.SILVER.ORDER_ITEMS;