variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "invoice_bucket_name" {
  description = "Name of the S3 bucket for incoming invoices"
  default     = "kraken-audit-invoices"
}

variable "report_bucket_name" {
  description = "Name of the S3 bucket for audit reports"
  default     = "kraken-audit-reports"
}

variable "google_api_key_secret" {
  description = "Name of the AWS Secrets Manager secret containing GOOGLE_API_KEY"
  default     = "kraken/google-api-key"
}