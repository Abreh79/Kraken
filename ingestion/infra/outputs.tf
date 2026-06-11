output "invoice_bucket" {
  description = "Upload invoices here to trigger Kraken"
  value       = aws_s3_bucket.invoice_bucket.id
}

output "report_bucket" {
  description = "Audit reports land here"
  value       = aws_s3_bucket.report_bucket.id
}

output "lambda_function_arn" {
  value = aws_lambda_function.ingestion_handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.ingestion_handler.function_name
}

output "trigger_info" {
  value = "Upload a PDF invoice to s3://${aws_s3_bucket.invoice_bucket.id}/ to auto-trigger the Kraken audit pipeline. Reports appear in s3://${aws_s3_bucket.report_bucket.id}/"
}