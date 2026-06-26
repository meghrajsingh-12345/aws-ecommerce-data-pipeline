import os
import boto3
import csv
import io

s3_client = boto3.client("s3")

# We dynamically send the clean file to your processed bucket output via environment vars
PROCESSED_BUCKET = "ecommerce-pipeline-478111024934-processed"

def lambda_handler(event, context):
    for record in event.get("Records", []):
        raw_bucket = record["s3"]["bucket"]["name"]
        raw_key = record["s3"]["object"]["key"]
        print(f"File discovered in landing zone: s3://{raw_bucket}/{raw_key}")
        
        # 1. Download the raw CSV data from S3
        response = s3_client.get_object(Bucket=raw_bucket, Key=raw_key)
        raw_content = response["Body"].read().decode("utf-8")
        
        # 2. Process / Clean the data natively
        # (This showcases your Python data manipulation skills to recruiters)
        input_data = csv.DictReader(io.StringIO(raw_content))
        output_buffer = io.StringIO()
        writer = csv.DictWriter(output_buffer, fieldnames=input_data.fieldnames)
        writer.writeheader()
        
        for row in input_data:
            # Drop rows with missing crucial identifiers or apply a clean format mutation
            if row.get("order_id") and row.get("order_id").strip():
                # Example cleaning: standardization step
                if "status" in row:
                    row["status"] = row["status"].upper()
                writer.writerow(row)
                
        # 3. Stream the processed clean file out to your golden bucket zone
        processed_key = raw_key.replace("raw-data/", "processed-data/")
        if not processed_key.startswith("processed-data/"):
            processed_key = f"processed-data/{processed_key}"
            
        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=processed_key,
            Body=output_buffer.getvalue()
        )
        print(f"Successfully cleaned data and stored at: s3://{PROCESSED_BUCKET}/{processed_key}")
        
    return {"statusCode": 200, "body": "Pipeline execution successful"}