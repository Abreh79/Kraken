provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "invoice_bucket" {
  bucket = var.bucket_name
}

resource "aws_iam_role" "lambda_role" {
  name = "ingestion_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "ingestion_handler" {
  filename      = "lambda_function_payload.zip"
  function_name = "invoice-ingestion-handler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "ingestion_handler.lambda_handler"

  runtime = "python3.11"

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion_handler.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.invoice_bucket.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.invoice_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.ingestion_handler.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}
