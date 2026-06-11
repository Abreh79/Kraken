provider "aws" {
  region = var.aws_region
}

# ─────────────────────────────────────────────
# S3 BUCKETS
# ─────────────────────────────────────────────

resource "aws_s3_bucket" "invoice_bucket" {
  bucket = var.invoice_bucket_name
}

resource "aws_s3_bucket" "report_bucket" {
  bucket = var.report_bucket_name
}

resource "aws_s3_bucket_versioning" "invoice_versioning" {
  bucket = aws_s3_bucket.invoice_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "report_versioning" {
  bucket = aws_s3_bucket.report_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "invoice_encrypt" {
  bucket = aws_s3_bucket.invoice_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "report_encrypt" {
  bucket = aws_s3_bucket.report_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ─────────────────────────────────────────────
# IAM ROLE & POLICIES
# ─────────────────────────────────────────────

resource "aws_iam_role" "lambda_role" {
  name = "kraken-ingestion-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy for S3 read on invoice bucket + write on report bucket
resource "aws_iam_policy" "s3_access" {
  name        = "kraken-s3-access"
  description = "Allow Kraken Lambda to read invoices and write reports"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject"]
        Resource = [
          "${aws_s3_bucket.invoice_bucket.arn}/*",
          "${aws_s3_bucket.invoice_bucket.arn}"
        ]
      },
      {
        Effect = "Allow"
        Action = ["s3:PutObject", "s3:PutObjectAcl"]
        Resource = [
          "${aws_s3_bucket.report_bucket.arn}/*",
          "${aws_s3_bucket.report_bucket.arn}"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3_access_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.s3_access.arn
}

# Policy for reading the GOOGLE_API_KEY from Secrets Manager
resource "aws_iam_policy" "secrets_access" {
  name        = "kraken-secrets-access"
  description = "Allow reading GOOGLE_API_KEY from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = ["arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.google_api_key_secret}*"]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.secrets_access.arn
}

# Lambda layer for ChromaDB (large dependency)
resource "aws_lambda_layer_version" "chromadb_layer" {
  filename   = "${path.module}/layers/chromadb-layer.zip"
  layer_name = "kraken-chromadb"

  compatible_runtimes = ["python3.11"]
  description         = "ChromaDB vector database for Kraken compliance engine"
}

# ─────────────────────────────────────────────
# LAMBDA FUNCTION
# ─────────────────────────────────────────────

resource "aws_lambda_function" "ingestion_handler" {
  filename      = "${path.module}/lambda_function_payload.zip"
  function_name = "kraken-ingestion-handler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 300  # 5 min for large PDFs + Gemini API
  memory_size   = 1024

  layers = [aws_lambda_layer_version.chromadb_layer.arn]

  environment {
    variables = {
      GOOGLE_API_KEY = "RESOLVED_VIA_SECRETS_MANAGER_AT_RUNTIME"
      REPORT_BUCKET  = aws_s3_bucket.report_bucket.id
      PYTHONPATH     = "/var/task"
    }
  }
}

# ─────────────────────────────────────────────
# S3 → LAMBDA TRIGGER
# ─────────────────────────────────────────────

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
    filter_prefix       = ""
    filter_suffix       = ""
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}

# ─────────────────────────────────────────────
# OUTPUTS
# ─────────────────────────────────────────────

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

output "trigger_info" {
  value = "Upload a PDF invoice to s3://${aws_s3_bucket.invoice_bucket.id}/ to auto-trigger the Kraken audit pipeline. Reports appear in s3://${aws_s3_bucket.report_bucket.id}/"
}