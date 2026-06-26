/* # glue.tf

# Logical "schema" that groups our tables together in the Glue Data Catalog
resource "aws_glue_catalog_database" "ecommerce_catalog" {
  name = "ecommerce_catalog"
}

# Crawler scans the PROCESSED bucket, infers the Parquet schema and
# partitions (order_year/order_month), and registers/updates a table
# in the Data Catalog so Athena can query it.
resource "aws_glue_crawler" "processed_crawler" {
  name          = "${var.project_name}-processed-crawler"
  role          = aws_iam_role.glue_role.arn
  database_name = aws_glue_catalog_database.ecommerce_catalog.name

  s3_target {
    path = "s3://${aws_s3_bucket.processed.bucket}/processed-data/"
  }

  # Re-crawl on a schedule so new partitions are picked up automatically.
  # cron syntax: run once a day at 06:00 UTC
  schedule = "cron(0 6 * * ? *)"

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }
}

# The actual PySpark ETL job definition
resource "aws_glue_job" "etl_job" {
  name              = "${var.project_name}-etl-job"
  role_arn          = aws_iam_role.glue_role.arn
  glue_version      = "4.0"
  worker_type       = var.glue_worker_type
  number_of_workers = var.glue_number_of_workers
  timeout           = 30 # minutes

  command {
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/scripts/etl_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--RAW_BUCKET"       = aws_s3_bucket.raw.bucket
    "--PROCESSED_BUCKET" = aws_s3_bucket.processed.bucket
    "--DATABASE_NAME"    = aws_glue_catalog_database.ecommerce_catalog.name
    "--TABLE_NAME"       = "orders_processed"
    "--job-language"     = "python"
    "--enable-metrics"   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
  }
}
*/