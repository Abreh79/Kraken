"""
AWS Lambda Handler — Kraken Audit Production Ingestion
Triggered by S3 bucket when a PDF invoice is uploaded.
Downloads the file, runs the full pipeline, uploads results.
"""

import os
import json
import tempfile
import logging
import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KrakenLambda")

s3 = boto3.client("s3")

ALLOWED_EXTENSIONS = {".pdf", ".jpeg", ".jpg", ".png"}
REPORT_BUCKET = os.environ.get("REPORT_BUCKET", "kraken-audit-reports")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


def lambda_handler(event, context):
    """S3-triggered Lambda: invoice upload → Kraken pipeline → report PDF."""
    logger.info(f"Event received: {json.dumps(event)}")

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        logger.info(f"Processing: s3://{bucket}/{key}")

        # Validate extension
        _, ext = os.path.splitext(key)
        if ext.lower() not in ALLOWED_EXTENSIONS:
            logger.warning(f"Skipping unsupported: {ext}")
            continue

        # Step 1: Download from S3
        tmp_invoice = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        try:
            s3.download_file(bucket, key, tmp_invoice.name)
            logger.info(f"Downloaded to {tmp_invoice.name}")
        except Exception as e:
            logger.error(f"Download failed: {e}")
            os.unlink(tmp_invoice.name)
            continue

        # Step 2: Run Kraken pipeline
        try:
            from kraken_audit.pipeline import Pipeline
            from kraken_audit.delivery.reporter import report_on_invoice
            import shutil

            # Setup ChromaDB path in /tmp (Lambda writable area)
            chroma_path = "/tmp/chroma_kb"
            kb_src = os.path.join(os.path.dirname(__file__), "..", "chroma_kb")
            if os.path.exists(kb_src) and not os.path.exists(chroma_path):
                shutil.copytree(kb_src, chroma_path)

            pipeline = Pipeline(api_key=GOOGLE_API_KEY, db_path=chroma_path)
            report_local = pipeline.process_invoice(tmp_invoice.name, show_dashboard=False)

            # Also generate PDF audit report if flags
            # (Pipeline already does this via reporter, but we upload it)
            inv_name = os.path.splitext(os.path.basename(key))[0]
            pdf_report_local = f"/tmp/audit_report_{inv_name}.pdf"

            # Upload Markdown report
            report_key = f"reports/{os.path.basename(report_local)}"
            s3.upload_file(report_local, REPORT_BUCKET, report_key)
            logger.info(f"Markdown report uploaded: s3://{REPORT_BUCKET}/{report_key}")

            # Upload PDF report if it exists
            pdf_report_expected = f"/home/team/shared/kraken_audit/docs/reports/audit_report_{inv_name}.pdf"
            if os.path.exists(pdf_report_expected):
                pdf_key = f"audit_reports/audit_report_{inv_name}.pdf"
                s3.upload_file(pdf_report_expected, REPORT_BUCKET, pdf_key)
                logger.info(f"PDF report uploaded: s3://{REPORT_BUCKET}/{pdf_key}")

            logger.info(f"Pipeline complete for {key}")

        except Exception as e:
            logger.error(f"Pipeline failed for {key}: {e}", exc_info=True)
        finally:
            os.unlink(tmp_invoice.name)

    return {"statusCode": 200, "body": json.dumps("Kraken Lambda processing complete")}