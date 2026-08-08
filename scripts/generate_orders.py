# Library Importation
import random
import pandas as pd
from faker import Faker
from pathlib import Path
from datetime import date
import sys

# Value Importation
from config import ORDER_GENERATION

fake = Faker()
orders = []

YEAR = int(sys.argv[1])
quarter = sys.argv[2]

QUARTER_DATES = {
    "Q1": (date(YEAR, 1, 1), date(YEAR, 3, 31)),
    "Q2": (date(YEAR, 4, 1), date(YEAR, 6, 30)),
    "Q3": (date(YEAR, 7, 1), date(YEAR, 9, 30)),
    "Q4": (date(YEAR, 10, 1), date(YEAR, 12, 31)),
}


NUMBER_OF_ORDERS = ORDER_GENERATION[quarter]["orders"]
start_order_id = ORDER_GENERATION[quarter]["start_order_id"]
start, end = QUARTER_DATES[quarter]

customers_df = pd.read_csv(f"data/raw/customers_{YEAR}.csv")
customers_df["signup_date"] = pd.to_datetime(
    customers_df["signup_date"],
)
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

output_path = Path(f"data/raw/orders_{YEAR}_{quarter}.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path, index=False)


print(f"{len(df)} orders generated.")
print(f"File saved to: {output_path}")

