""" IMPORTATION """
import random
import pandas as pd
from faker import Faker
from pathlib import Path
from datetime import date
import sys

fake = Faker()
orders = []

quarter = sys.argv[1]
year = int(sys.argv[2])
NUMBER_OF_ORDERS = int(sys.argv[3])
start_order_id = int(sys.argv[4])

QUARTERS = {
    "Q1": (date(year, 1, 1), date(year, 3, 31)),
    "Q2": (date(year, 4, 1), date(year, 6, 30)),
    "Q3": (date(year, 7, 1), date(year, 9, 30)),
    "Q4": (date(year, 10, 1), date(year, 12, 31)),
}

start, end = QUARTERS[quarter]

customers_df = pd.read_csv("data/raw/customers.csv")
customers_df["signup_date"] = pd.to_datetime(customers_df["signup_date"])
customers_df = customers_df[
    customers_df["signup_date"] <= pd.Timestamp(end)
]

for order_id in range(start_order_id, NUMBER_OF_ORDERS + start_order_id):
    random_customer = customers_df.sample(1)
    order_start= max(
                        random_customer.iloc[0]["signup_date"].date(),
                        start
                    )
    orders.append({
        "order_id": order_id,
        "customer_id": random_customer.iloc[0]["customer_id"], 
        "order_date": fake.date_between(start_date= order_start, end_date=end)
    })

df = pd.DataFrame(orders)

output_path = Path(f"data/raw/orders_{year}_{quarter}.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path, index=False)


print(f"{len(df)} orders generated.")
print(f"File saved to: {output_path}")