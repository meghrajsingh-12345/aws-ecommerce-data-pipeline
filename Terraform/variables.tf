variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix used when naming all resources, for easy identification/cleanup"
  type        = string
  default     = "ecommerce-pipeline"
}

variable "alert_email" {
  description = "Email address subscribed to the SNS topic for pipeline failure alerts"
  type        = string
  default     = "you@example.com"
}

variable "glue_worker_type" {
  description = "Glue worker type. G.1X is the cheapest standard option, good for learning/demo workloads."
  type        = string
  default     = "G.1X"
}

variable "glue_number_of_workers" {
  description = "Number of Glue workers to provision for the ETL job"
  type        = number
  default     = 2
}
