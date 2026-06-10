import os
import google.generativeai as genai
from .models import InvoiceData
import json

class GeminiExtractor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY must be provided or set as environment variable")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash') # Using 2.5 Flash

    def extract(self, file_path: str) -> InvoiceData:
        # Upload file to Gemini if needed or pass directly as bytes
        # For simplicity and multi-modal support, we'll pass the image bytes
        
        with open(file_path, "rb") as f:
            image_data = f.read()

        prompt = """
        Extract all information from this HVAC invoice and return it in a strict JSON format matching this schema:
        {
            "metadata": { 
                "vendor_name": "...", 
                "invoice_date": "...", 
                "invoice_id": "...",
                "total_amount": 0.0,
                "currency": "..."
            },
            "labor_items": [ { "technician_identifier": "...", "task_description": "...", "billing_rate_hourly": 0.0, "hours_billed": 0.0, "line_total": 0.0 } ],
            "parts_and_materials": [ { "description": "...", "quantity": 0.0, "unit_cost": 0.0, "line_total": 0.0 } ],
            "vague_charges": [ { "charge_type": "...", "description": "...", "amount": 0.0 } ]
        }
        
        Rules:
        - If a field is missing, use null.
        - Labor items should specifically capture technician names and their rates.
        - Vague charges are things like 'Service Fee', 'Truck Charge', 'Environmental Fee' without clear hourly or unit breakdown.
        - Ensure numerical values are floats.
        """

        response = self.model.generate_content([
            prompt,
            {"mime_type": "image/png", "data": image_data}
        ], generation_config={"response_mime_type": "application/json"})

        try:
            data = json.loads(response.text)
            return InvoiceData(**data)
        except Exception as e:
            # Fallback or error handling
            print(f"Error parsing Gemini response: {e}")
            print(f"Raw response: {response.text}")
            raise
