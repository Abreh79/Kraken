import os
import json
import logging
import uuid
import subprocess
import shutil
from unittest.mock import patch
from kraken_audit.pipeline import Pipeline
from kraken_audit.extraction.models import InvoiceData

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestIntegration")

def run_db_query(sql):
    """Helper to run team-db queries and return results with retries for locking."""
    import time
    max_retries = 5
    for i in range(max_retries):
        result = subprocess.run(["team-db", sql], capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout.strip() else []
        if "locked" in result.stderr.lower() and i < max_retries - 1:
            logger.warning(f"Database locked, retrying ({i+1}/{max_retries})...")
            time.sleep(2)
            continue
    return []

def test_integration():
    """
    Comprehensive Integration Test following lead's instructions:
    1. Uses mock extraction JSON from tests/fixtures/mock_extraction.json
    2. Feeds it through the compliance engine
    3. Feeds augmented data through the delivery node (via Pipeline.process_invoice)
    4. Asserts 3 violations, report generation, and DB records.
    5. Cleans up test data.
    """
    logger.info("Starting Integration Test with Mock JSON")
    
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mock_json_path = os.path.join(base_dir, "tests", "fixtures", "mock_extraction.json")
    local_db_path = os.path.join(os.path.expanduser("~"), f"chroma_db_test_{uuid.uuid4().hex[:6]}")
    
    # Load mock data
    with open(mock_json_path, "r") as f:
        mock_data_dict = json.load(f)
    
    mock_invoice_data = InvoiceData.model_validate(mock_data_dict)
    unique_invoice_id = mock_invoice_data.metadata.invoice_id
    unique_vendor = mock_invoice_data.metadata.vendor_name
    
    pipeline = Pipeline(api_key="mock_key", db_path=local_db_path)
    
    # 1. Check DB count before execution
    initial_count_resp = run_db_query("SELECT count(*) FROM audit_invoices")
    initial_count = initial_count_resp[0].get("count (*)", 0) if initial_count_resp else 0
    logger.info(f"Initial record count in audit_invoices: {initial_count}")

    # 2. Mock external dependencies
    # Mock run_extraction to return our loaded mock data
    with patch('kraken_audit.pipeline.run_extraction', return_value=mock_invoice_data):
        # Mock Compliance KnowledgeBase ingestion to avoid dependency on PDF file presence
        with patch('kraken_audit.judge.compliance_engine.KnowledgeBase.ingest_pdf'):
            
            # Create a dummy incoming file
            test_file = f"/home/team/shared/invoices/incoming/test_{unique_invoice_id}.pdf"
            os.makedirs(os.path.dirname(test_file), exist_ok=True)
            with open(test_file, "w") as f:
                f.write("mock content for integration test")
            
            try:
                # --- EXECUTE PIPELINE ---
                report_path = pipeline.process_invoice(test_file)
                logger.info(f"Pipeline executed successfully. Report generated at: {report_path}")
                
                # --- VERIFY REPORT ---
                assert os.path.exists(report_path), "Report file should exist"
                with open(report_path, "r") as f:
                    content = f.read()
                    assert unique_vendor in content, "Vendor name missing from report"
                    assert unique_invoice_id in content, "Invoice ID missing from report"
                    assert "Labor Cap" in content, "Labor Cap rule should have triggered"
                    assert "Vague Billing" in content, "Vague Billing rule should have triggered"
                    assert "Role Discrepancy" in content, "Role Discrepancy rule should have triggered"
                
                # --- VERIFY DATABASE RECORDS ---
                # Check that a new record was added
                final_count_resp = run_db_query("SELECT count(*) FROM audit_invoices")
                final_count = final_count_resp[0].get("count (*)", 0) if final_count_resp else 0
                assert final_count == initial_count + 1, "A new invoice record should be created in the DB"
                
                # Verify the specific invoice record content
                db_records = run_db_query(f"SELECT * FROM audit_invoices WHERE invoice_number = '{unique_invoice_id}'")
                assert len(db_records) >= 1, f"Should find record with invoice_number {unique_invoice_id}"
                # If there are multiple (from previous failed runs), we take the last one
                record = db_records[-1]
                internal_db_id = record["id"]
                assert record["vendor_name"] == unique_vendor
                
                # Verify that all 3 flags were persisted to the flags table
                flags = run_db_query(f"SELECT * FROM audit_compliance_flags WHERE invoice_id = '{internal_db_id}'")
                assert len(flags) == 3, "Database should contain 3 compliance flags for this invoice"
                
                flag_types = [f["flag_type"] for f in flags]
                assert "Labor Cap" in flag_types
                assert "Vague Billing" in flag_types
                assert "Role Discrepancy" in flag_types
                
                logger.info("Integration Test PASSED!")
                    
            finally:
                # --- CLEANUP ---
                logger.info("Cleaning up test artifacts...")
                if os.path.exists(test_file):
                    os.remove(test_file)
                if 'report_path' in locals() and os.path.exists(report_path):
                    os.remove(report_path)
                
                if os.path.exists(local_db_path):
                    shutil.rmtree(local_db_path)
                
                # Cleanup DB records
                if 'internal_db_id' in locals():
                    run_db_query(f"DELETE FROM audit_compliance_flags WHERE invoice_id = '{internal_db_id}'")
                    run_db_query(f"DELETE FROM audit_invoices WHERE id = '{internal_db_id}'")
                    logger.info("Database records cleaned up.")

if __name__ == "__main__":
    try:
        test_integration()
    except Exception as e:
        logger.error(f"Integration Test FAILED: {e}", exc_info=True)
        exit(1)
