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
