import os
import json
import logging
import uuid
import subprocess
from unittest.mock import MagicMock, patch
from kraken_audit.pipeline import Pipeline
from kraken_audit.extraction.models import InvoiceData, Metadata, LaborItem, PartItem, VagueCharge

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestPipeline")

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
        raise Exception(f"Database error: {result.stderr}")

def test_pipeline_e2e():
    """
    Comprehensive End-to-End Integration Test.
    Covers:
    - Pipeline orchestration flow
    - Schema mapping and field alignment
    - Triggering of all 3 compliance rules (Labor Cap, Vague Billing, Role Discrepancy)
    - Markdown report generation
    - Database persistence (Invoices and Flags)
    """
    logger.info("Starting Comprehensive E2E Pipeline Test")
    
    # Use unique identifiers to avoid collisions in shared DB
    unique_vendor = f"Test HVAC Corp {uuid.uuid4().hex[:6]}"
    unique_invoice_id = f"INV-{uuid.uuid4().hex[:6]}"
    
    # Use a local path for ChromaDB to avoid permission issues in shared folders during tests
    local_db_path = os.path.join(os.path.expanduser("~"), f"chroma_db_test_{uuid.uuid4().hex[:6]}")
    pipeline = Pipeline(api_key="mock_key", db_path=local_db_path)
    
    # Construct mock data that triggers all three compliance rules
    mock_invoice_data = InvoiceData(
        metadata=Metadata(
            vendor_name=unique_vendor,
            invoice_date="2026-06-10",
            invoice_id=unique_invoice_id,
            total_amount=2500.0,
            currency="USD"
        ),
        labor_items=[
            # Triggers Rule 1: Labor Cap ($150 > $95)
            # Triggers Rule 3: Role Discrepancy (Master Tech on simple task 'Filter swap')
            LaborItem(
                technician_identifier="Master Tech Alice",
                task_description="Filter swap and basic inspection",
                billing_rate_hourly=150.0,
                hours_billed=2.0,
                line_total=300.0
            )
        ],
        parts_and_materials=[],
        vague_charges=[
            # Triggers Rule 2: Vague Billing (MISC $750 > $500)
            VagueCharge(
                charge_type="MISC",
                description="Miscellaneous Lot fee",
                amount=750.0
            )
        ]
    )

    # 1. Check DB count before execution
    initial_count = run_db_query("SELECT count(*) FROM audit_invoices")[0].get("count (*)", 0)
    logger.info(f"Initial record count in audit_invoices: {initial_count}")

    # 2. Mock external dependencies
    # Mock run_extraction to return our crafted mock data
    with patch('kraken_audit.pipeline.run_extraction', return_value=mock_invoice_data):
        # Mock Compliance KnowledgeBase ingestion to avoid dependency on PDF file presence
        with patch('kraken_audit.judge.compliance_engine.KnowledgeBase.ingest_pdf'):
            
            # Create a dummy incoming file
            test_file = f"/home/team/shared/invoices/incoming/test_{unique_invoice_id}.pdf"
            os.makedirs(os.path.dirname(test_file), exist_ok=True)
            with open(test_file, "w") as f:
                f.write("mock content")
            
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
                final_count = run_db_query("SELECT count(*) FROM audit_invoices")[0].get("count (*)", 0)
                assert final_count == initial_count + 1, "A new invoice record should be created in the DB"
                
                # Verify the specific invoice record content
                db_records = run_db_query(f"SELECT * FROM audit_invoices WHERE invoice_number = '{unique_invoice_id}'")
                assert len(db_records) == 1, f"Should find exactly one record with invoice_number {unique_invoice_id}"
                internal_db_id = db_records[0]["id"]
                assert db_records[0]["vendor_name"] == unique_vendor
                assert db_records[0]["total_amount"] == 2500.0
                
                # Verify that all 3 flags were persisted to the flags table
                flags = run_db_query(f"SELECT * FROM audit_compliance_flags WHERE invoice_id = '{internal_db_id}'")
                assert len(flags) == 3, "Database should contain 3 compliance flags for this invoice"
                
                flag_types = [f["flag_type"] for f in flags]
                assert "Labor Cap" in flag_types
                assert "Vague Billing" in flag_types
                assert "Role Discrepancy" in flag_types
                
                logger.info("End-to-End Pipeline Integration Test PASSED!")
                    
            finally:
                # --- CLEANUP ---
                logger.info("Cleaning up test artifacts...")
                if os.path.exists(test_file):
                    os.remove(test_file)
                if 'report_path' in locals() and os.path.exists(report_path):
                    os.remove(report_path)
                
                import shutil
                if os.path.exists(local_db_path):
                    shutil.rmtree(local_db_path)
                
                # Cleanup DB records
                if 'internal_db_id' in locals():
                    run_db_query(f"DELETE FROM audit_compliance_flags WHERE invoice_id = '{internal_db_id}'")
                    run_db_query(f"DELETE FROM audit_invoices WHERE id = '{internal_db_id}'")
                    logger.info("Database records cleaned up.")

def test_watcher_trigger():
    """
    Test that the file watcher correctly triggers the pipeline when a new file is detected.
    """
    logger.info("Starting Watcher Trigger Test")
    unique_id = uuid.uuid4().hex[:8]
    incoming_dir = "/home/team/shared/invoices/incoming"
    processed_dir = "/home/team/shared/invoices/processed"
    test_file = os.path.join(incoming_dir, f"watcher_test_{unique_id}.pdf")
    report_file = os.path.join(processed_dir, f"report_INV-{unique_id}.md")
    
    # Mock data for the orchestrator inside the watcher
    mock_invoice_data = InvoiceData(
        metadata=Metadata(
            vendor_name="Watcher Test Corp",
            invoice_date="2026-06-10",
            invoice_id=f"INV-{unique_id}",
            total_amount=100.0,
            currency="USD"
        ),
        labor_items=[],
        parts_and_materials=[],
        vague_charges=[]
    )

    # Start the watcher in a background process using the venv python
    python_exe = os.path.join(os.path.expanduser("~"), "venv/bin/python")
    if not os.path.exists(python_exe):
        python_exe = "python3" # Fallback

    # We need to mock things globally for the subprocess or just let it run 
    # but that's hard. Better to test the IntegratedWatcher class directly.
    
    from kraken_audit.watcher_integrated import IntegratedWatcher
    from watchdog.events import FileCreatedEvent
    
    # Mock the Pipeline class before initializing IntegratedWatcher
    with patch('kraken_audit.watcher_integrated.Pipeline') as MockPipeline:
        mock_pipeline_instance = MockPipeline.return_value
        mock_pipeline_instance.process_invoice.return_value = report_file
        
        watcher = IntegratedWatcher(incoming_dir)
        
        # Drop the file
        os.makedirs(incoming_dir, exist_ok=True)
        with open(test_file, "w") as f:
            f.write("trigger watcher")
            
        try:
            # Simulate the event
            event = FileCreatedEvent(test_file)
            watcher.on_created(event)
            
            # Verify pipeline was called
            mock_pipeline_instance.process_invoice.assert_called_once_with(test_file)
            logger.info("Watcher trigger test PASSED!")
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

if __name__ == "__main__":
    try:
        test_pipeline_e2e()
        print("\n" + "="*50 + "\n")
        test_watcher_trigger()
    except Exception as e:
        logger.error(f"Test FAILED: {e}", exc_info=True)
        exit(1)
