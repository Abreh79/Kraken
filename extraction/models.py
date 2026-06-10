from pydantic import BaseModel, Field
from typing import List, Optional

class Metadata(BaseModel):
    vendor_name: Optional[str] = Field(None, description="The name of the vendor")
    invoice_date: Optional[str] = Field(None, description="The date of the invoice")
    invoice_id: Optional[str] = Field(None, description="The invoice number or ID")
    total_amount: Optional[float] = Field(None, description="The total amount of the invoice")
    currency: Optional[str] = Field("USD", description="The currency of the invoice")

class LaborItem(BaseModel):
    technician_identifier: Optional[str] = Field(None, description="Name or ID of the technician")
    task_description: Optional[str] = Field(None, description="Description of the work performed")
    billing_rate_hourly: Optional[float] = Field(None, description="Hourly rate charged")
    hours_billed: Optional[float] = Field(None, description="Number of hours billed")
    line_total: Optional[float] = Field(None, description="Total for this line item")

class PartItem(BaseModel):
    description: Optional[str] = Field(None, description="Description of the part or material")
    quantity: Optional[float] = Field(None, description="Quantity used")
    unit_cost: Optional[float] = Field(None, description="Cost per unit")
    line_total: Optional[float] = Field(None, description="Total for this line item")

class VagueCharge(BaseModel):
    charge_type: Optional[str] = Field(None, description="Type of charge (e.g., service fee, environmental fee)")
    description: Optional[str] = Field(None, description="Description of the charge")
    amount: Optional[float] = Field(None, description="Amount of the charge")

class InvoiceData(BaseModel):
    metadata: Metadata
    labor_items: List[LaborItem] = Field(default_factory=list)
    parts_and_materials: List[PartItem] = Field(default_factory=list)
    vague_charges: List[VagueCharge] = Field(default_factory=list)
