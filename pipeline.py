import os
import json
import logging
from kraken_audit.extraction.engine import run_extraction
from kraken_audit.judge.compliance_engine import ComplianceEngine
from kraken_audit.delivery.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Pipeline")

class Pipeline:
    def __init__(self, api_key=None, db_path=None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.compliance_engine = ComplianceEngine(db_path=db_path)
        self.report_gen = ReportGenerator()

    def process_invoice(self, file_path):
        logger.info(f"Starting pipeline for: {file_path}")
        
        try:
            # 1. Extraction Stage
            logger.info("Stage 1: Extraction")
            invoice_data_obj = run_extraction(file_path, api_key=self.api_key)
            # Convert Pydantic model to dict
            invoice_dict = invoice_data_obj.model_dump()
            logger.info(f"Extraction successful: {invoice_dict['metadata'].get('invoice_id')}")

            # 2. Compliance Stage
            logger.info("Stage 2: Compliance")
            # Compliance engine expects dict, returns JSON string
            augmented_json_str = self.compliance_engine.evaluate(invoice_dict)
            augmented_data = json.loads(augmented_json_str)
            logger.info(f"Compliance check complete. Flags found: {len(augmented_data.get('compliance_flags', []))}")

            # 3. Delivery Stage (with mapping)
            logger.info("Stage 3: Delivery")
            final_payload = self.map_to_delivery_schema(augmented_data)
            
            # Persist to DB
            invoice_db_id = self.report_gen.persist_invoice(final_payload)
            logger.info(f"Persisted to database with ID: {invoice_db_id}")
            
            # Generate Report
            report_md = self.report_gen.generate_markdown_report(final_payload)
            invoice_number = final_payload["invoice_metadata"].get("invoice_number", "unknown")
            report_path = f"/home/team/shared/invoices/processed/report_{invoice_number}.md"
            with open(report_path, "w") as f:
                f.write(report_md)
            
            logger.info(f"Report generated: {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"Pipeline failed for {file_path}: {e}", exc_info=True)
            raise

    def map_to_delivery_schema(self, data):
        """
        Maps the Compliance Engine output to the Delivery Node input schema.
        Handles field name misalignments.
        """
        metadata = data.get("metadata", {})
        
        # 1. Map Metadata
        invoice_metadata = {
            "vendor_name": metadata.get("vendor_name", "Unknown Vendor"),
            "invoice_number": metadata.get("invoice_id", "N/A"),
            "invoice_date": metadata.get("invoice_date", "N/A"),
            "total_amount": metadata.get("total_amount", 0.0),
            "currency": metadata.get("currency", "USD")
        }

        # 2. Map Extraction Data (mostly passthrough but renamed key)
        extraction_data = {
            "labor_items": data.get("labor_items", []),
            "parts_and_materials": data.get("parts_and_materials", []),
            "vague_charges": data.get("vague_charges", [])
        }

        # 3. Map Compliance Results
        compliance_results = []
        for flag in data.get("compliance_flags", []):
            compliance_results.append({
                "flag_type": flag.get("rule_violated", "Compliance Flag"),
                "severity": flag.get("severity", "medium"),
                "description": flag.get("description", ""),
                "estimated_savings": flag.get("estimated_overcharge", 0.0)
            })

        return {
            "invoice_metadata": invoice_metadata,
            "extraction_data": extraction_data,
            "compliance_results": compliance_results
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        orchestrator = Pipeline()
        orchestrator.process_invoice(path)
    else:
        print("Usage: python orchestrator.py <file_path>")
