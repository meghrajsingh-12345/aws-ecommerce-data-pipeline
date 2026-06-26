# s3.tf
# Four buckets, each with a single clear purpose. Splitting them up (instead of
# using one bucket with prefixes) makes IAM policies simpler to scope tightly,
# and makes lifecycle rules (e.g. auto-archiving raw data) easier to apply
# independently per bucket.

locals {
  account_id  = data.aws_caller_identity.current.account_id
  bucket_name = "${var.project_name}-${local.account_id}"
}

# 1. RAW bucket — landing zone for untouched source files
resource "aws_s3_bucket" "raw" {
  bucket = "${local.bucket_name}-raw"
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 2. PROCESSED bucket — cleaned, partitioned Parquet output of the Glue job
resource "aws_s3_bucket" "processed" {
  bucket = "${local.bucket_name}-processed"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "processed" {
  bucket = aws_s3_bucket.processed.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "processed" {
  bucket                  = aws_s3_bucket.processed.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 3. SCRIPTS bucket — holds the Glue PySpark script that Glue jobs read from
resource "aws_s3_bucket" "scripts" {
  bucket = "${local.bucket_name}-scripts"
}

resource "aws_s3_object" "etl_script" {
  bucket = aws_s3_bucket.scripts.id
  key    = "scripts/etl_job.py"
  source = "${path.module}/../glue/etl_job.py"
  etag   = filemd5("${path.module}/../glue/etl_job.py")
}

# 4. ATHENA RESULTS bucket — Athena writes query result files here
resource "aws_s3_bucket" "athena_results" {
  bucket = "${local.bucket_name}-athena-results"
}

resource "aws_s3_bucket_lifecycle_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "expire-old-query-results"
    status = "Enabled"

    # Applies the rule to all objects in the bucket, satisfying validation constraints
    filter {}

    expiration {
      days = 30
    }
  }
}

# S3 event notification: every new object in raw/ triggers the Lambda function
resource "aws_s3_bucket_notification" "raw_upload_trigger" {
  bucket = aws_s3_bucket.raw.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.trigger_glue.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw-data/"
    filter_suffix       = ".csv"
  }

  # Critical dependency: Forces Lambda IAM permission rules to activate BEFORE 
  # AWS attempts to validate this trigger configuration.
  depends_on = [
    aws_lambda_permission.allow_s3_invoke
  ]
}