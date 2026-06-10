# Kraken Audit - Delivery Node

This module handles the final stage of the Kraken Audit pipeline: persisting audited invoice data and generating professional reports.

## Files
- `report_generator.py`: The main class for persistence and report generation.
- `audit_invoices`: Database table (in Turso) for main invoice records.
- `audit_compliance_flags`: Database table (in Turso) for specific compliance flags.

## Usage

### As a Python Module

```python
from report_generator import ReportGenerator

# Data should be the compliance-augmented JSON from The Judge
data = {
    "invoice_metadata": { ... },
    "extraction_data": { ... },
    "compliance_results": [ ... ]
}

gen = ReportGenerator()

# 1. Persist to database
invoice_id = gen.persist_invoice(data)

# 2. Generate Markdown report
report_md = gen.generate_markdown_report(data)

# 3. Save report to file
with open(f"report_{data['invoice_metadata']['invoice_number']}.md", "w") as f:
    f.write(report_md)
```

## Database Schema

### `audit_invoices`
- `id`: Primary Key (UUID)
- `vendor_name`: Name of the HVAC vendor
- `invoice_number`: Vendor's invoice number
- `invoice_date`: Date on the invoice
- `total_amount`: Total amount billed
- `currency`: Currency (default 'USD')
- `extraction_json`: Full JSON payload (metadata + extraction + compliance)
- `created_at`: Timestamp of audit completion

### `audit_compliance_flags`
- `id`: Primary Key (UUID)
- `invoice_id`: Foreign Key to `audit_invoices`
- `flag_type`: Type of discrepancy (e.g., Overcharge, Vague Billing)
- `description`: Detailed explanation of the flag
- `estimated_savings`: Estimated dollar amount for cost recovery
- `severity`: high, medium, or low
