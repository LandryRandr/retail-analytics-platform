# Import Library
import subprocess
from pathlib import Path
import sys

# Import Value
from upload_to_s3 import upload_file

YEAR = sys.argv[1]
quarter = sys.argv[2]


def generate_master_data():

    generated_files = []

    if not Path("data/raw/products.csv").exists():
        print("Generating products...")
        subprocess.run(
            ["python3", "scripts/generate_products.py"],
            check=True
        )
        generated_files.append("data/raw/products.csv")
    else:
        print("Products already exist.")

    if not Path(f"data/raw/customers_{YEAR}.csv").exists():
        print("Generating customers...")
        subprocess.run(
            ["python3", "scripts/generate_customers.py", YEAR],
            check=True
        )
        generated_files.append(f"data/raw/customers_{YEAR}.csv")
    else:
        print("Customers already exist.")
    
    return generated_files


def generate_transactions():

    orders_file = f"data/raw/orders_{YEAR}_{quarter}.csv"
    order_items_file = f"data/raw/order_items_{YEAR}_{quarter}.csv"

    subprocess.run(
        ["python3", "scripts/generate_orders.py", YEAR, quarter],
        check=True
    )

    subprocess.run(
        ["python3", "scripts/generate_order_items.py", YEAR, quarter],
        check=True
    )
    return [
        orders_file,
        order_items_file
    ]


def upload_generated_files():

    upload_file("data/raw/products.csv")

    upload_file(f"data/raw/customers_{YEAR}.csv")

    upload_file(
        f"data/raw/orders_{YEAR}_{quarter}.csv"
    )

    upload_file(
        f"data/raw/order_items_{YEAR}_{quarter}.csv"
    )



def main():

    print("========== Retail Analytics Pipeline ==========")

    generated_master_files = generate_master_data()

    generate_transaction_files = generate_transactions()

    file_to_upload = (
        generated_master_files + generate_transaction_files
    )

    for file in file_to_upload:
        upload_file(file)

    print("========= Pipeline completed successfully. =========")


if __name__ == "__main__":
    main()