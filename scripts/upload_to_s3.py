# Import Library
from pathlib import Path
import boto3

# Import value
from config import BUCKET_NAME

s3 = boto3.client("s3")


def upload_file(file_path: str):

    path = Path(file_path)
    filename = path.name
    stem = path.stem

    # PRODUCTS
    if stem == "products":
        dataset = "products"
        s3_key = (
            f"raw/{dataset}/{filename}"
        )

    # CUSTOMERS
    elif stem.startswith("customers_"):
        dataset = "customers"
        parts = stem.split("_")
        year = parts[1]
        s3_key = (
            f"raw/{dataset}/"
            f"year={year}/"
            f"{filename}"
        )

    # ORDERS
    elif stem.startswith("orders_"):
        dataset = "orders"
        parts = stem.split("_")
        year = parts[1]
        quarter = parts[2]
        s3_key = (
            f"raw/{dataset}/"
            f"year={year}/"
            f"quarter={quarter}/"
            f"{filename}"
        )

    # ORDER ITEMS
    elif stem.startswith("order_items_"):
        dataset = "order_items"
        parts = stem.split("_")
        year = parts[2]
        quarter = parts[3]
        s3_key = (
            f"raw/{dataset}/"
            f"year={year}/"
            f"quarter={quarter}/"
            f"{filename}"
        )

    else:

        raise ValueError(
            f"Unknown file format: {filename}"
        )


    # UPLOAD

    s3.upload_file(
        str(path),
        BUCKET_NAME,
        s3_key
    )

    print(f"Uploaded: {filename}")
    print(
        f"Destination: "
        f"s3://{BUCKET_NAME}/{s3_key}"
    )