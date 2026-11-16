# Retail Analytics Platform

An end-to-end retail data analytics platform demonstrating data generation, cloud data ingestion, data warehousing, transformation, dimensional modelling, and business intelligence.

This project simulates a retail business environment and implements a modern data pipeline using Python, Amazon S3, Snowflake, and Streamlit.

The objective is to transform raw retail data into structured, analytics-ready datasets and deliver actionable business insights through interactive dashboards.

---

Project Architecture

The platform follows a layered data architecture:

              DATA GENERATION
                    |
                    v
             Python Scripts
                    |
                    v
               CSV Files
                    |
                    v
             Amazon S3 Bucket
                 (raw/)
                    |
                    v
          Snowflake External Stage
                    |
                    v
          Snowflake External Tables
                    |
                    v
              SILVER LAYER
          Data Ingestion & Processing
                    |
                    v
               GOLD LAYER
        Analytical Tables & Data Marts
                    |
                    v
            Streamlit Dashboard
                    |
                    v
             Business Insights

Data Flow

1. Data Generation: Python scripts generate synthetic retail datasets.
2. Cloud Storage: Generated CSV files are uploaded to Amazon S3.
3. Data Access: Snowflake accesses the files through an external stage and external tables.
4. Data Processing: The SILVER layer structures and processes incoming data.
5. Data Modelling: The GOLD layer provides analytical tables and business views.
6. Data Visualization: A Streamlit dashboard queries the GOLD layer to display business performance indicators.

---

Technology Stack

Category| Technologies
Programming| Python
Data Generation| Faker, Pandas
Cloud Storage| Amazon S3
Data Warehouse| Snowflake
Data Ingestion| Snowflake External Stages & External Tables
Data Transformation| SQL, Stored Procedures
Workflow Automation| Snowflake Tasks
Business Intelligence| Streamlit, Altair
Data Analysis| Pandas, NumPy
Version Control| Git, GitHub

---

Repository Structure

retail-analytics-platform/
│
├── dashboards/
│   ├── streamlit_app_1.py
│   ├── streamlit_app_2.py
│   └── streamlit_app_3.py
│
├── docs/
│   ├── aws_instructions.txt
│   ├── External_Stage_Retail_Analytics_Snowflake_AWS.txt
│   └── github_instructions.txt
│
├── scripts/
│   ├── config.py
│   ├── generate_all.py
│   ├── generate_customers.py
│   ├── generate_order_items.py
│   ├── generate_orders.py
│   ├── generate_products.py
│   └── upload_to_s3.py
│
├── sql/
│   ├── 01_database and schemas.sql
│   ├── 02_file_formats.sql
│   ├── 03_external_stages.sql
│   ├── 04_external_tables.sql
│   ├── 05_silver_tables.sql
│   ├── 06_00_Silver_manual_ingestion.sql
│   ├── 06_01_Silver_insert_procedures.sql
│   ├── 06_03_Tasks.sql
│   ├── 07_01_gold_tables.sql
│   ├── 07_02_Gold_procedure.sql
│   └── 08_gold_views.sql
│
├── requirements.txt
└── README.md

---

Data Model

The project uses a layered data architecture to separate source data, processing logic, and analytical datasets.

External Data Layer

The external data layer provides access to CSV files stored in Amazon S3.

It uses:

- Snowflake Storage Integration
- External Stage
- CSV File Formats
- External Tables

SILVER Layer

The SILVER layer contains structured datasets prepared for analytical processing.

Its responsibilities include:

- Data ingestion from external tables.
- Data organization and standardization.
- Structured storage in Snowflake.
- Ingestion tracking and processing logic.

GOLD Layer

The GOLD layer contains business-oriented analytical structures.

The main objects include:

- "FACT_SALES"
- "DIM_CUSTOMER"
- "DIM_PRODUCT"

Business views are also provided to simplify analytical queries:

- "V_SALES"
- "V_SALES_BY_PRODUCT"
- "V_SALES_BY_MONTH"
- "V_SALES_BY_CUSTOMER"

The dimensional model is designed to support sales reporting and business intelligence analysis.

---

Business Intelligence Dashboard

The selected desktop-oriented dashboard is:

"dashboards/streamlit_app_2.py"

It connects to Snowflake and retrieves data from the GOLD layer.

Dashboard Features

Key Performance Indicators

- Total Revenue
- Total Orders
- Average Basket Value
- Month-over-Month Revenue Growth
- Unique Customers
- Repeat Customer Rate

Sales Analysis

- Daily revenue trends
- Seven-day moving average
- Monthly seasonality
- Revenue evolution over time

Product Analysis

- Top-performing products
- Product revenue contribution
- Category performance
- Sales mix analysis

Interactive Filters

- Year
- Country
- Product Category

The dashboard is designed to help users explore business performance and identify useful commercial trends.

---

Getting Started

1. Clone the Repository

git clone https://github.com/LandryRandr/retail-analytics-platform.git

cd retail-analytics-platform

2. Create a Python Virtual Environment

Linux / macOS:

python -m venv .venv

source .venv/bin/activate

Windows PowerShell:

python -m venv .venv

.venv\Scripts\Activate.ps1

3. Install Dependencies

python -m pip install --upgrade pip

python -m pip install -r requirements.txt

The current "requirements.txt" contains dependencies for the Python data-generation and S3-upload scripts.

The Snowflake-hosted dashboard requires its own compatible runtime dependencies.

4. Configure AWS

Configure AWS credentials for the identity used by the Python upload script.

The uploader must have the necessary permissions to write objects to the target S3 bucket and raw prefix.

Do not store AWS access keys or secret keys directly in Python scripts or commit them to GitHub.

5. Generate Retail Data

The generation scripts are located in:

scripts/

The main orchestration script is:

python scripts/generate_all.py

Review "scripts/config.py" and the generation scripts before execution to understand the dataset configuration and output locations.

6. Upload Data to Amazon S3

The upload script is:

python scripts/upload_to_s3.py

Make sure the AWS credentials, bucket name, and destination prefix are correctly configured before uploading.

7. Configure Snowflake

Execute the SQL scripts located in:

sql/

The scripts cover:

1. Database and schema creation.
2. File format configuration.
3. External stage creation.
4. External table creation.
5. SILVER table creation.
6. Data ingestion procedures.
7. Task configuration.
8. GOLD analytical tables and procedures.
9. Business views.

Additional AWS and Snowflake configuration instructions are available in:

docs/

8. Deploy the Dashboard

The selected dashboard is:

dashboards/streamlit_app_2.py

It uses Snowpark's "get_active_session()" and is intended to run as a Streamlit application within Snowflake.

The Snowflake execution context must have permission to query the required GOLD objects.

---

AWS and Snowflake Security

The architecture separates the AWS identity used for uploading data from the IAM role assumed by Snowflake.

Python uploader

Requires the permissions needed to upload files to the designated S3 location.

Snowflake Storage Integration

Uses a dedicated IAM role with the required read and listing permissions for the source data.

Security recommendations:

- Never commit AWS access keys or secret keys.
- Never publish Snowflake passwords or private credentials.
- Use IAM least-privilege permissions.
- Keep local environment files out of version control.
- Avoid unnecessary write or delete permissions for Snowflake's read-only integration.
- Review resource identifiers and IAM policies before deployment.

---

Project Objectives

This project was developed to demonstrate practical skills in:

- Building an end-to-end data pipeline.
- Generating and managing structured datasets.
- Integrating Python with AWS S3.
- Connecting cloud storage to Snowflake.
- Designing layered data architectures.
- Developing SQL transformations and stored procedures.
- Automating data processing with Snowflake Tasks.
- Building analytical data models.
- Developing interactive business intelligence dashboards.
- Managing a data engineering project using Git and GitHub.

---

Current Project Status

The repository contains the main components of the intended data pipeline, including Python scripts, AWS/Snowflake integration scripts, SQL processing logic, and Streamlit dashboards.

The project is still evolving.

A complete end-to-end production validation, including automated tests, cloud permissions, scheduled processing, and dashboard deployment, remains necessary before considering the platform production-ready.

---

Author

Landry Randr

Aspiring Data & BI Analyst | Data Engineering

Technologies: Python · SQL · Snowflake · AWS · Power BI · Streamlit

GitHub: "LandryRandr" (https://github.com/LandryRandr)

---

Built as a hands-on portfolio project to explore modern cloud data engineering and business intelligence practices.