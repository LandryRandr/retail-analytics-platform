import pandas as pd
import random
from pathlib import Path

CATEGORIES = {
    "Smartphones": [
        "iPhone",
        "Galaxy",
        "Pixel",
        "Xiaomi",
        "OnePlus",
        "Motorola",
        "Huawei",
        "Nothing",
        "Oppo",
        "Realme"
    ],

    "Laptops": [
        "Dell XPS",
        "MacBook Air",
        "MacBook Pro",
        "HP Spectre",
        "Lenovo ThinkPad",
        "ASUS ZenBook",
        "Acer Swift",
        "MSI Prestige",
        "Surface Laptop",
        "LG Gram"
    ],

    "Smartwatches": [
        "Apple Watch",
        "Galaxy Watch",
        "Garmin",
        "Fitbit",
        "Huawei Watch",
        "Amazfit",
        "Pixel Watch",
        "Suunto",
        "Polar",
        "Coros"
    ],

    "Audio": [
        "Sony Headphones",
        "JBL Speaker",
        "Bose Speaker",
        "AirPods",
        "Galaxy Buds",
        "Marshall Speaker",
        "Anker Speaker",
        "Beats",
        "Sennheiser",
        "Jabra"
    ],

    "Solar Equipment": [
        "Solar Panel 100W",
        "Solar Panel 200W",
        "Solar Charger",
        "Portable Solar Kit",
        "Solar Battery",
        "Solar Controller",
        "Solar Inverter",
        "Roof Panel",
        "Camping Panel",
        "Eco Panel"
    ],

    "Batteries": [
        "Power Bank 10000",
        "Power Bank 20000",
        "AA Battery Pack",
        "AAA Battery Pack",
        "Laptop Battery",
        "Camera Battery",
        "Drone Battery",
        "UPS Battery",
        "Rechargeable Cells",
        "Portable Battery"
    ],

    "Chargers": [
        "USB-C Charger",
        "Wireless Charger",
        "Laptop Charger",
        "Fast Charger",
        "Car Charger",
        "Multi-Port Charger",
        "GaN Charger",
        "Travel Adapter",
        "Wall Adapter",
        "Power Adapter"
    ],

    "Accessories": [
        "Phone Case",
        "Tempered Glass",
        "Laptop Sleeve",
        "Wireless Mouse",
        "Mechanical Keyboard",
        "USB Hub",
        "Webcam",
        "Microphone",
        "Docking Station",
        "HDMI Cable"
    ],

    "Monitors": [
        "Dell Monitor",
        "LG UltraWide",
        "Samsung Monitor",
        "ASUS Monitor",
        "BenQ Monitor",
        "AOC Monitor",
        "ViewSonic",
        "MSI Monitor",
        "HP Monitor",
        "Curved Monitor"
    ],

    "Televisions": [
        "Samsung OLED",
        "LG OLED",
        "Sony Bravia",
        "TCL QLED",
        "Hisense TV",
        "Philips TV",
        "Panasonic TV",
        "Sharp TV",
        "Xiaomi TV",
        "Amazon Fire TV"
    ]
}


PRICE_RANGES = {
    "Smartphones": (300, 1500),
    "Laptops": (700, 2500),
    "Smartwatches": (100, 800),
    "Audio": (30, 600),
    "Solar Equipment": (150, 3000),
    "Batteries": (20, 300),
    "Chargers": (15, 120),
    "Accessories": (10, 150),
    "Monitors": (150, 1200),
    "Televisions": (250, 4000),
}


products = []

product_id = 0

for category, product_names in CATEGORIES.items() :
    minimum, maximum = PRICE_RANGES[category]
    for product_name in product_names :
        product_id +=1
        products.append({
            "product_id" : product_id,
            "product_name" : product_name,
            "category" : category,
            "unit_price" : round(random.uniform(minimum, maximum), 2)
        })

df = pd.DataFrame(products)

output_path = Path("data/raw/products.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path, index=False)

print(f"{len(df)} products generated.")
print(f"File saved to : {output_path}")