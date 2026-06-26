"""
etl_job.py
----------
AWS Glue (PySpark) ETL job.

Responsibilities:
  1. Read raw CSV order data from the "raw" S3 bucket.
  2. Clean it (drop duplicates/nulls, fix types, normalize text).
  3. Enrich it (derive total_amount, order_year, order_month).
  4. Write it back out as partitioned Parquet in the "processed" bucket.

Why Parquet + partitioning?
  - Parquet is columnar -> Athena/Redshift only scan the columns a
    query actually needs, which is both faster and cheaper than CSV.
  - Partitioning by year/month means a query filtered to a single
    month only scans that month's files, not the entire dataset.
    This directly reduces Athena's "$5 per TB scanned" cost.

This script is designed to run as a Glue job (Glue 4.0 / Spark 3.x),
but the core PySpark logic is portable and could run on EMR too.
"""

import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import col, month, to_date, trim, upper, year
from pyspark.sql.types import DoubleType, IntegerType

# --- Job setup -------------------------------------------------------------
args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "RAW_BUCKET", "PROCESSED_BUCKET", "DATABASE_NAME", "TABLE_NAME"],
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

raw_path = f"s3://{args['RAW_BUCKET']}/raw-data/"
processed_path = f"s3://{args['PROCESSED_BUCKET']}/processed-data/"

print(f"Reading raw data from: {raw_path}")

# --- Extract ----------------------------------------------------------------
df_raw = (
    spark.read.option("header", True)
    .option("inferSchema", True)
    .csv(raw_path)
)

row_count_raw = df_raw.count()
print(f"Raw row count: {row_count_raw}")

# --- Transform / Clean -------------------------------------------------------
df_clean = (
    df_raw
    # Remove exact duplicate orders (simulated upstream re-sends)
    .dropDuplicates(["order_id"])
    # Drop rows missing critical identifiers
    .na.drop(subset=["order_id", "customer_id", "order_date"])
    # Normalize category text (fixes "Electronics" vs "ELECTRONICS")
    .withColumn("category", upper(trim(col("category"))))
    # Cast numeric fields safely; non-numeric values become null
    .withColumn("unit_price", col("unit_price").cast(DoubleType()))
    .withColumn("quantity", col("quantity").cast(IntegerType()))
    # Parse date string into a real date type
    .withColumn("order_date", to_date(col("order_date"), "yyyy-MM-dd"))
)

# Drop rows that failed numeric/date casting or have invalid business values
df_clean = df_clean.filter(
    (col("unit_price").isNotNull())
    & (col("quantity").isNotNull())
    & (col("quantity") > 0)
    & (col("order_date").isNotNull())
)

# --- Enrich -------------------------------------------------------------------
df_final = (
    df_clean
    .withColumn("total_amount", col("unit_price") * col("quantity"))
    .withColumn("order_year", year(col("order_date")))
    .withColumn("order_month", month(col("order_date")))
)

row_count_final = df_final.count()
print(f"Clean row count: {row_count_final} (dropped {row_count_raw - row_count_final} rows)")

# --- Load ----------------------------------------------------------------------
print(f"Writing partitioned Parquet to: {processed_path}")

(
    df_final.write.mode("overwrite")
    .partitionBy("order_year", "order_month")
    .parquet(processed_path)
)

print("ETL job complete.")
job.commit()
