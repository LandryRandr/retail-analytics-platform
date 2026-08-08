from faker import Faker
import pandas as pd
from pathlib import Path
import sys


fake = Faker()
NUMBER_OF_CUSTOMERS = 600
customers = []

year = sys.argv[1]

for customer_id in range(1, NUMBER_OF_CUSTOMERS + 1):
    customers.append({
        "customer_id": customer_id,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "city": fake.city(),
        "country": fake.country(),
        "signup_date": fake.date_between(start_date="-5y", end_date="today")
    })

df = pd.DataFrame(customers)

output_path = Path(f"data/raw/customers_{year}.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path, index=False)

print(f"{len(df)} customers generated.")
print(f"File saved to: {output_path}")