import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .knowledge_base import KnowledgeBase

class ComplianceFlag(BaseModel):
    rule_violated: str
    severity: str
    description: str
    estimated_overcharge: float

class ComplianceEngine:
    def __init__(self, labor_cap: float = 95.0, vague_threshold: float = 500.0, db_path: str = None):
        self.labor_cap = labor_cap
        self.vague_threshold = vague_threshold
        self.vague_keywords = ["LOT", "MISC", "FUEL SURCHARGE"]
        
        if db_path is None:
            # Default to a local path if not provided
            db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        
        self.kb = KnowledgeBase(db_path=db_path)
        
        # Try to ingest the Fortress PDF if it exists in expected locations
        potential_paths = [
            "/home/team/shared/Ultimate_HVAC_Knowledge_Fortress.pdf",
            "/home/team/shared/kraken_audit/Ultimate_HVAC_Knowledge_Fortress.pdf",
            os.path.join(os.path.dirname(__file__), "Ultimate_HVAC_Knowledge_Fortress.pdf")
        ]
        for path in potential_paths:
            if os.path.exists(path):
                self.kb.ingest_pdf(path)
                break

    def check_labor_cap(self, labor_items: List[Dict[str, Any]]) -> List[ComplianceFlag]:
        flags = []
        for item in labor_items:
            rate = item.get("billing_rate_hourly")
            hours = item.get("hours_billed", 0)
            if rate and rate > self.labor_cap:
                overcharge = (rate - self.labor_cap) * (hours or 0)
                flags.append(ComplianceFlag(
                    rule_violated="Labor Cap",
                    severity="high",
                    description=f"Billing rate ${rate}/hr exceeds cap of ${self.labor_cap}/hr",
                    estimated_overcharge=float(overcharge)
                ))
        return flags

    def check_vague_billing(self, vague_charges: List[Dict[str, Any]]) -> List[ComplianceFlag]:
        flags = []
        for charge in vague_charges:
            desc = charge.get("description", "").upper()
            amount = charge.get("amount", 0)
            if any(kw in desc for kw in self.vague_keywords) and amount > self.vague_threshold:
                flags.append(ComplianceFlag(
                    rule_violated="Vague Billing",
                    severity="medium",
                    description=f"Vague charge '{charge.get('description')}' exceeds ${self.vague_threshold} without itemization",
                    estimated_overcharge=float(amount)
                ))
        return flags

    def check_role_discrepancy(self, labor_items: List[Dict[str, Any]]) -> List[ComplianceFlag]:
        flags = []
        simple_tasks = ["filter swap", "preventive maintenance", "standard maintenance", "visual inspection", "filter replacement"]
        
        for item in labor_items:
            tech_id = item.get("technician_identifier", "").lower()
            task_desc = item.get("task_description", "").lower()
            
            # Rule: Master tech should not be billed for simple tasks
            is_master = "master" in tech_id
            is_simple = any(task in task_desc for task in simple_tasks)
            
            if is_master and is_simple:
                # We flag it. In a more advanced version, we query KB for "standard rates for simple tasks"
                flags.append(ComplianceFlag(
                    rule_violated="Role Discrepancy",
                    severity="medium",
                    description=f"Master level technician ('{item.get('technician_identifier')}') billed for simple task: '{item.get('task_description')}'",
                    estimated_overcharge=0.0  # Would require knowing the difference between Master and Apprentice rates
                ))
            
            # Cross-reference with Knowledge Base (Vector DB)
            if task_desc:
                kb_info = self.kb.query(task_desc, n_results=1)
                # This could be used to validate if the hours billed match the expected time for the task
                # or if the technician level is appropriate according to the 'Fortress'
                pass
                
        return flags

    def evaluate(self, invoice_json: str) -> str:
        if isinstance(invoice_json, str):
            data = json.loads(invoice_json)
        else:
            data = invoice_json
            
        labor_items = data.get("labor_items", [])
        vague_charges = data.get("vague_charges", [])
        
        flags = []
        flags.extend(self.check_labor_cap(labor_items))
        flags.extend(self.check_vague_billing(vague_charges))
        flags.extend(self.check_role_discrepancy(labor_items))
        
        data["compliance_flags"] = [flag.model_dump() for flag in flags]
        return json.dumps(data, indent=2)

if __name__ == "__main__":
    # Test with dummy data
    test_data = {
        "metadata": {"invoice_id": "INV-TEST-999"},
        "labor_items": [
            {"technician_identifier": "Master Tech John", "task_description": "Filter swap and standard preventive maintenance", "billing_rate_hourly": 120.0, "hours_billed": 2.0}
        ],
        "vague_charges": [
            {"charge_type": "MISC", "description": "Miscellaneous LOT fee", "amount": 600.0}
        ]
    }
    engine = ComplianceEngine()
    result = engine.evaluate(test_data)
    print(result)
