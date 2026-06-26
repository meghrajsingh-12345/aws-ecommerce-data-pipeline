terraform {
  required_version = ">= 1.5.0"

  # Your active remote cloud backend
  backend "s3" {
    bucket       = "meghraj-aws-tfstate-2026"
    key          = "ecommerce-pipeline/state.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true   # This uses S3's native locking instead of DynamoDB!
  }

  # Your project's required cloud plugins
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}
# Fetches your active AWS account ID, user ARN, and credentials dynamically
data "aws_caller_identity" "current" {}