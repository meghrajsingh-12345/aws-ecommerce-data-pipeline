"""
generate_sample_data.py
------------------------
Simulates a daily extract from an e-commerce order system.

In a real company, this CSV would instead come from:
  - a transactional database export (e.g. nightly RDS/Postgres dump)
  - an API pull from a payments/orders platform
  - a third-party SFTP drop

For this project, we generate it locally so anyone can run the
pipeline end-to-end without needing access to a real production system.

Usage:
    python generate_sample_data.py --rows 5000 --out orders.csv
"""

import argparse
import csv
import random
from datetime import datetime, timedelta

CATEGORIES = ["Electronics", "Apparel", "Home & Kitchen", "Books", "Sports", "Toys", "Beauty"]
PRODUCTS = {
    "Electronics": ["Wireless Earbuds", "Bluetooth Speaker", "Phone Charger", "Smartwatch"],
    "Apparel": ["T-Shirt", "Jeans", "Hoodie", "Sneakers"],
    "Home & Kitchen": ["Blender", "Air Fryer", "Coffee Maker", "Cutlery Set"],
    "Books": ["Fiction Novel", "Cookbook", "Self-Help Book", "Comic Book"],
    "Sports": ["Yoga Mat", "Dumbbell Set", "Running Shoes", "Cycling Helmet"],
    "Toys": ["Building Blocks", "Puzzle Set", "RC Car", "Board Game"],
    "Beauty": ["Face Cream", "Shampoo", "Lipstick", "Perfume"],
}
REGIONS = ["NORTH", "SOUTH", "EAST", "WEST"]


def random_date(start_days_ago=180):
    start = datetime.now() - timedelta(days=start_days_ago)
    random_offset = random.randint(0, start_days_ago)
    return (start + timedelta(days=random_offset)).strftime("%Y-%m-%d")


def generate_rows(n):
    rows = []
    for i in range(1, n + 1):
        category = random.choice(CATEGORIES)
        product = random.choice(PRODUCTS[category])
        unit_price = round(random.uniform(5, 500), 2)
        quantity = random.randint(1, 5)

        # Intentionally inject some "dirty" data so the Glue ETL job
        # has real cleaning work to do (this mirrors real-world data quality issues)
        if random.random() < 0.02:
            unit_price = ""  # missing price
        if random.random() < 0.01:
            quantity = -1  # bad quantity

        rows.append({
            "order_id": f"ORD{i:06d}",
            "customer_id": f"CUST{random.randint(1, 1200):05d}",
            "order_date": random_date(),
            "product_name": product,
            "category": category.upper() if random.random() < 0.5 else category,  # inconsistent casing
            "unit_price": unit_price,
            "quantity": quantity,
            "region": random.choice(REGIONS),
        })

    # Inject a handful of exact duplicate rows to simulate upstream re-sends
    for _ in range(max(1, n // 200)):
        rows.append(random.choice(rows).copy())

    random.shuffle(rows)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=5000, help="Number of order rows to generate")
    parser.add_argument("--out", type=str, default="orders.csv", help="Output CSV filename")
    args = parser.parse_args()

    fieldnames = ["order_id", "customer_id", "order_date", "product_name",
                  "category", "unit_price", "quantity", "region"]

    rows = generate_rows(args.rows)
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} rows -> {args.out}")
    print("Upload it with:")
    print(f"  aws s3 cp {args.out} s3://<your-raw-bucket>/raw-data/{args.out}")


if __name__ == "__main__":
    main()
