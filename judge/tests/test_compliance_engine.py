import sys
import os
import json

# Add shared directory to path
sys.path.append("/home/team/shared")

from kraken_audit.compliance.compliance_engine import ComplianceEngine

def test_engine():
    # Mock extraction data
    invoice_data = {
        "metadata": {
            "vendor_name": "Pro HVAC Solutions",
            "invoice_date": "2026-06-09",
            "invoice_id": "INV-KB-001"
        },
        "labor_items": [
            {
                "technician_identifier": "Master Technician Alice",
                "task_description": "Standard preventive maintenance and filter swap",
                "billing_rate_hourly": 110.0,
                "hours_billed": 3.0,
                "line_total": 330.0
            },
            {
                "technician_identifier": "Apprentice Bob",
                "task_description": "Assisted in maintenance",
                "billing_rate_hourly": 60.0,
                "hours_billed": 3.0,
                "line_total": 180.0
            }
        ],
        "parts_and_materials": [
            {
                "description": "Standard MERV 13 Filters",
                "quantity": 4.0,
                "unit_cost": 25.0,
                "line_total": 100.0
            }
        ],
        "vague_charges": [
            {
                "charge_type": "MISC",
                "description": "LOT materials and small parts",
                "amount": 550.0
            },
            {
                "charge_type": "FUEL",
                "description": "FUEL SURCHARGE",
                "amount": 45.0
            }
        ]
    }

    print("Initializing Compliance Engine...")
    engine = ComplianceEngine(labor_cap=95.0, vague_threshold=500.0)
    
    print("Running evaluation...")
    result_json = engine.evaluate(invoice_data)
    result = json.loads(result_json)
    
    print("\n--- Compliance Results ---")
    flags = result.get("compliance_flags", [])
    if not flags:
        print("No flags found.")
    for flag in flags:
        print(f"[{flag['rule_violated']}] Severity: {flag['severity']}")
        print(f"  Description: {flag['description']}")
        print(f"  Estimated Overcharge: ${flag['estimated_overcharge']}")
    
    # Check if expected flags are present
    rules_flagged = [f['rule_violated'] for f in flags]
    assert "Labor Cap" in rules_flagged
    assert "Vague Billing" in rules_flagged
    assert "Role Discrepancy" in rules_flagged
    print("\nAll expected rules were triggered successfully!")

if __name__ == "__main__":
    try:
        test_engine()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
