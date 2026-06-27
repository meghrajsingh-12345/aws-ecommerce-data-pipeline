import boto3
import csv
import io

s3_client = boto3.client("s3")

# Processed bucket
PROCESSED_BUCKET = "ecommerce-pipeline-478111024934-processed"


def lambda_handler(event, context):
    for record in event.get("Records", []):
        raw_bucket = record["s3"]["bucket"]["name"]
        raw_key = record["s3"]["object"]["key"]

        print(f"Processing file: s3://{raw_bucket}/{raw_key}")

        # Download raw CSV
        response = s3_client.get_object(
            Bucket=raw_bucket,
            Key=raw_key
        )

        raw_content = response["Body"].read().decode("utf-8")

        # Read CSV
        input_data = csv.DictReader(io.StringIO(raw_content))

        output_buffer = io.StringIO()

        writer = csv.DictWriter(
            output_buffer,
            fieldnames=input_data.fieldnames
        )

        writer.writeheader()

        # Used to remove duplicate order_ids
        seen_orders = set()

        for row in input_data:

            # Skip rows without order_id
            order_id = row.get("order_id", "").strip()

            if not order_id:
                continue

            # Remove duplicate order IDs
            if order_id in seen_orders:
                continue

            seen_orders.add(order_id)

            # Remove rows with missing price
            unit_price = row.get("unit_price", "").strip()

            if not unit_price:
                continue

            # Validate quantity
            try:
                quantity = int(row.get("quantity", 0))

                if quantity <= 0:
                    continue

            except (ValueError, TypeError):
                continue

            # Validate price
            try:
                row["unit_price"] = f"{float(unit_price):.2f}"

            except (ValueError, TypeError):
                continue

            # Standardize category casing
            category = row.get("category", "").strip()

            if category:
                row["category"] = category.title()

            # Write cleaned row
            writer.writerow(row)

        # Destination file
        processed_key = raw_key.replace(
            "raw-data/",
            "processed-data/"
        )

        if not processed_key.startswith("processed-data/"):
            processed_key = f"processed-data/{processed_key}"

        # Upload cleaned CSV
        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=processed_key,
            Body=output_buffer.getvalue()
        )

        print(
            f"Cleaned file uploaded to s3://{PROCESSED_BUCKET}/{processed_key}"
        )

    return {
        "statusCode": 200,
        "body": "Pipeline execution successful"
    }
