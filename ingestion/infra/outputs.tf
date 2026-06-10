output "bucket_name" {
  value = aws_s3_bucket.invoice_bucket.id
}

output "lambda_function_arn" {
  value = aws_lambda_function.ingestion_handler.arn
}
