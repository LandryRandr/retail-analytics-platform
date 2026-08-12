-- INGESTION CONRTOL
CREATE TABLE IF NOT EXISTS RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
    source_file VARCHAR(1000) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT PK_INGESTION_LOG
        PRIMARY KEY (source_file, target_table)
);


DESC TABLE RETAIL_ANALYTICS.SILVER.INGESTION_LOG;


-- INSPECTION OF THE EXTERNAL ORDERS
SELECT
    METADATA$FILENAME AS source_file,
    COUNT(*) AS row_count
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDERS
GROUP BY METADATA$FILENAME
ORDER BY source_file;


-- Checking the Ingestion log
SELECT *
FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG;



/*  =====
            ORDERS SILVER TABLE
                                ====*/



--===================================
-- Manual Ingestion Q1
--===================================

-- INGESTION Q1
INSERT INTO RETAIL_ANALYTICS.SILVER.ORDERS (
    order_id,
    customer_id,
    order_date,
    year,
    quarter
)
SELECT
    order_id,
    customer_id,
    order_date,
    year,
    quarter
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDERS
WHERE METADATA$FILENAME =
    'raw/orders/year=2024/quarter=Q1/orders_2024_Q1.csv';


SELECT COUNT(*)
FROM RETAIL_ANALYTICS.SILVER.ORDERS;


-- RECORD THE PROCESSED FILE (Q1)
INSERT INTO RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
    SOURCE_FILE,
    TARGET_TABLE
)
VALUES (
    'raw/orders/year=2024/quarter=Q1/orders_2024_Q1.csv',
    'ORDERS'
);


-- VERIFICATION OF THE FIRST CYCLE
SELECT *
FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG;

-- VERIFY THE RESULT
SELECT
    source_file,
    target_table,
    loaded_at
FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG
ORDER BY loaded_at;


SELECT COUNT(*) AS SILVER_ORDER_COUNT
FROM RETAIL_ANALYTICS.SILVER.ORDERS;




--===================================
-- ORDERS- Manual Ingestion Q2
--===================================

-- INGESTION (Q2)
INSERT INTO RETAIL_ANALYTICS.SILVER.ORDERS (
    order_id,
    customer_id,
    order_date,
    year,
    quarter
)
SELECT
    order_id,
    customer_id,
    order_date,
    year,
    quarter
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDERS
WHERE METADATA$FILENAME =
    'raw/orders/year=2024/quarter=Q2/orders_2024_Q2.csv';


-- RECORD THE PROCESSED FILE (Q2)
INSERT INTO RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
    SOURCE_FILE,
    TARGET_TABLE
)
VALUES (
    'raw/orders/year=2024/quarter=Q2/orders_2024_Q2.csv',
    'ORDERS'
);


-- VERIFICATION
SELECT COUNT(*) AS SILVER_ORDER_COUNT
FROM RETAIL_ANALYTICS.SILVER.ORDERS;

SELECT *
FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG;


TRUNCATE TABLE RETAIL_ANALYTICS.SILVER.ORDERS;
DELETE FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG
WHERE TARGET_TABLE = 'ORDERS';


-- TEST IDOMPOTENCY
INSERT INTO RETAIL_ANALYTICS.SILVER.ORDERS (
    order_id,
    customer_id,
    order_date,
    year,
    quarter
)
SELECT
    order_id,
    customer_id,
    order_date,
    year,
    quarter
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDERS e
WHERE e.METADATA$FILENAME =
      'raw/orders/year=2024/quarter=Q2/orders_2024_Q2.csv'
  AND NOT EXISTS (
      SELECT 1
      FROM RETAIL_ANALYTICS.SILVER.ORDERS s
      WHERE s.order_id = e.order_id
  );



/*  =====
            ORDER_ITEMS SILVER TABLE
                                      ====*/

-- VERIFICATION
SELECT *
FROM RETAIL_ANALYTICS.SILVER.ORDER_ITEMS
LIMIT 10;

SELECT
    year,
    quarter,
    COUNT(*) AS row_count,
    COUNT(DISTINCT order_id || '-' || product_id) AS distinct_keys
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDER_ITEMS
GROUP BY year, quarter
ORDER BY year, quarter;

SELECT
    order_id,
    product_id,
    COUNT(*) AS cnt
FROM RETAIL_ANALYTICS.RAW_EXT.EXTERNAL_ORDER_ITEMS
GROUP BY order_id, product_id
HAVING COUNT(*) > 1
ORDER BY cnt DESC;


-- INGESTION - ORDER_ITEMS Q1 
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
WHERE e.METADATA$FILENAME =
      'raw/order_items/year=2024/quarter=Q1/order_items_2024_Q1.csv'
  AND NOT EXISTS (
      SELECT 1
      FROM RETAIL_ANALYTICS.SILVER.ORDER_ITEMS s
      WHERE s.order_id = e.order_id
        AND s.product_id = e.product_id
  );



-- RECORD THE FILE Q1
INSERT INTO RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
    SOURCE_FILE,
    TARGET_TABLE
)
SELECT
    'raw/order_items/year=2024/quarter=Q1/order_items_2024_Q1.csv',
    'ORDER_ITEMS'
WHERE NOT EXISTS (
    SELECT 1
    FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG
    WHERE SOURCE_FILE =
          'raw/order_items/year=2024/quarter=Q1/order_items_2024_Q1.csv'

);



-- INGESTION ORDER_ITEMS Q2
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
WHERE e.METADATA$FILENAME =
      'raw/order_items/year=2024/quarter=Q2/order_items_2024_Q2.csv'
  AND NOT EXISTS (
      SELECT 1
      FROM RETAIL_ANALYTICS.SILVER.ORDER_ITEMS s
      WHERE s.order_id = e.order_id
        AND s.product_id = e.product_id
  );


-- VERIFICATION
SELECT
    year,
    quarter,
    COUNT(*) AS row_count
FROM RETAIL_ANALYTICS.SILVER.ORDER_ITEMS
GROUP BY year, quarter
ORDER BY year, quarter;


-- RECORD THE FILE Q2
INSERT INTO RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
    SOURCE_FILE,
    TARGET_TABLE
)
SELECT
    'raw/order_items/year=2024/quarter=Q2/order_items_2024_Q2.csv',
    'ORDER_ITEMS'
WHERE NOT EXISTS (
    SELECT 1
    FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG
    WHERE SOURCE_FILE =
          'raw/order_items/year=2024/quarter=Q2/order_items_2024_Q2.csv'
      AND TARGET_TABLE = 'ORDER_ITEMS'
);


SELECT *
FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG;




/*  =====
            CUSTOMERS SILVER TABLE
                                      ====*/

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
WHERE e.METADATA$FILENAME =
      'raw/customers/year=2024/customers_2024.csv'

  AND NOT EXISTS (
      SELECT 1
      FROM RETAIL_ANALYTICS.SILVER.CUSTOMERS s
      WHERE s.CUSTOMER_ID = e.CUSTOMER_ID
  );


-- RECORDING THE FILE
INSERT INTO RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
    SOURCE_FILE,
    TARGET_TABLE
)
SELECT
    'raw/customers/year=2024/customers_2024.csv',
    'CUSTOMERS'
WHERE NOT EXISTS (
    SELECT 1
    FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG
    WHERE SOURCE_FILE =
          'raw/customers/year=2024/customers_2024.csv'
      AND TARGET_TABLE = 'CUSTOMERS'
);



/*  =====
            PRODUCT SILVER TABLE
                                      ====*/

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
WHERE e.METADATA$FILENAME =
      'raw/products/products.csv'
  AND NOT EXISTS (
      SELECT 1
      FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG l
      WHERE l.SOURCE_FILE = e.METADATA$FILENAME
        AND l.TARGET_TABLE = 'PRODUCTS'
  )
  AND NOT EXISTS (
      SELECT 1
      FROM RETAIL_ANALYTICS.SILVER.PRODUCTS s
      WHERE s.PRODUCT_ID = e.PRODUCT_ID
  );


-- RECORDING THE FILE
INSERT INTO RETAIL_ANALYTICS.SILVER.INGESTION_LOG (
    SOURCE_FILE,
    TARGET_TABLE
)
SELECT
    'raw/products/products.csv',
    'PRODUCTS'
WHERE NOT EXISTS (
    SELECT 1
    FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG
    WHERE SOURCE_FILE = 'raw/products/products.csv'
      AND TARGET_TABLE = 'PRODUCTS'
);


SELECT *
FROM RETAIL_ANALYTICS.SILVER.INGESTION_LOG;



