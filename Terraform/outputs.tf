output "raw_bucket_name" {
  description = "S3 bucket to upload raw CSV files into"
  value       = aws_s3_bucket.raw.bucket
}

output "processed_bucket_name" {
  description = "S3 bucket where cleaned Parquet output lands"
  value       = aws_s3_bucket.processed.bucket
}

output "scripts_bucket_name" {
  value = aws_s3_bucket.scripts.bucket
}

output "athena_results_bucket_name" {
  value = aws_s3_bucket.athena_results.bucket
}

output "lambda_function_name" {
  value = aws_lambda_function.trigger_glue.function_name
}

output "athena_workgroup_name" {
  value = aws_athena_workgroup.ecommerce_wg.name
}

output "sns_alert_topic_arn" {
  value = aws_sns_topic.pipeline_alerts.arn
}