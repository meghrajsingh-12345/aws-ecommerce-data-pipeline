# lambda.tf

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/trigger_glue_job.py"
  output_path = "${path.module}/build/trigger_glue_job.zip"
}

resource "aws_lambda_function" "trigger_glue" {
  function_name    = "${var.project_name}-trigger-glue"
  role             = aws_iam_role.lambda_role.arn
  handler          = "trigger_glue_job.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      GLUE_JOB_NAME = "ecommerce-pipeline-etl-job"
    }
  }
}

# Grants S3 permission to invoke this specific Lambda function.
# Without this, S3 bucket notifications silently fail.
resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger_glue.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw.arn
}
# Grants Lambda the explicit permission to kick off the AWS Glue ETL job
resource "aws_iam_role_policy" "lambda_glue_policy" {
  name = "${var.project_name}-lambda-glue-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns"
        ]
        Resource = "*"
      }
    ]
  })
}
