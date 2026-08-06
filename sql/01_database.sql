/* IDOMPOTENT */
create database IF NOT EXISTS RETAIL_ANALYTICS;
USE DATABASE RETAIL_ANALYTICS;
CREATE SCHEMA IF NOT EXISTS BRONZE;
CREATE SCHEMA IF NOT EXISTS SILVER;
CREATE SCHEMA IF NOT EXISTS GOLD;


USE DATABASE RETAIL_ANALYTICS;

USE SCHEMA BRONZE;

-- ======================================
-- CUSTOMERS
-- ======================================
CREATE OR REPLACE TABLE CUSTOMERS (
    customer_id INTEGER,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    signup_date DATE
);

-- ======================================
-- PRODUCTS
-- ======================================
CREATE OR REPLACE TABLE PRODUCTS (
    product_id INTEGER,
    product_name VARCHAR(150),
    category VARCHAR(100),
    unit_price NUMBER(10,2)
);

-- ======================================
-- ORDERS
-- ======================================
CREATE OR REPLACE TABLE ORDERS (
    order_id INTEGER,
    customer_id INTEGER,
    order_date DATE
);

-- ======================================
-- ORDER_ITEMS
-- ======================================
CREATE OR REPLACE TABLE ORDER_ITEMS (
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    unit_price NUMBER(10,2)
);


