from datetime import date
import sys

BUCKET_NAME = "retail-analytics-s3-218712444577"
RAW_PREFIX = "raw"

ORDER_GENERATION = {
    "Q1": {
        "orders": 400,
        "start_order_id": 1
    },
    "Q2": {
        "orders": 700,
        "start_order_id": 401
    },
    "Q3": {
        "orders": 500,
        "start_order_id": 1101
    },
    "Q4": {
        "orders": 1000,
        "start_order_id": 1601
    }
}