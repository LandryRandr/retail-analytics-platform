import random
import pandas as pd
from pathlib import Path
import sys

quarter = sys.argv[1]
year = int(sys.argv[2])

orders_df = pd.read_csv(
    f"data/raw/orders_{year}_{quarter}.csv"
)

products_df = pd.read_csv(
    "data/raw/products.csv"
)

order_items = []

for order_id in orders_df["order_id"] :
    chosen_products = random.sample(
        list(products_df["product_id"]), 
        random.randint(1, 10)
    )
    for product in chosen_products :
        quantity = random.randint(1, 3)

        product_row = products_df[
            products_df["product_id"] == product
        ].iloc[0]

        order_items.append({
            "order_id" : order_id,
            "product_id" : product,
            "quantity" : quantity,
            "unit_price" : product_row["unit_price"]
        })

df = pd.DataFrame(order_items)


output_path = Path(f"data/raw/order_items_{year}_{quarter}.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path, index=False)

print(f"{len(df)} order items generated.")
print(f"File saved to: {output_path}")


