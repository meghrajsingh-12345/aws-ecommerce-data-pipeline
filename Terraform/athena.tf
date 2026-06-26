# athena.tf
# A dedicated workgroup keeps this project's query history and result
# location separate from any other Athena usage in the same AWS account,
# and lets you set per-workgroup cost controls (bytes-scanned limits).
resource "aws_athena_workgroup" "ecommerce_wg" {
  name = "${var.project_name}-workgroup"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/results/"
    }

    bytes_scanned_cutoff_per_query = 1073741824 # 1 GB safety cap per query
  }
}

# sns.tf (kept in this file for simplicity) — alerting on pipeline failures
resource "aws_sns_topic" "pipeline_alerts" {
  name = "${var.project_name}-alerts"
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.pipeline_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch alarm: fires if the Glue job has a failed run
resource "aws_cloudwatch_metric_alarm" "glue_job_failure" {
  alarm_name          = "${var.project_name}-glue-job-failure"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "glue.driver.aggregate.numFailedTasks"
  namespace           = "Glue"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Triggers when the Glue ETL job has failed tasks"
  alarm_actions       = [aws_sns_topic.pipeline_alerts.arn]

  dimensions = {
    JobName = "ecommerce-pipeline-etl-job"
    JobRunId = "ALL"
  }

  treat_missing_data = "notBreaching"
}
