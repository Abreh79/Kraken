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

    def extract(self, file_paths) -> InvoiceData:
        """
        Extract invoice data from one or more image paths (multi-page support).
        Accepts a single path string or a list of paths.
        """
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        # Build Gemini content parts: prompt + all page images
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
        - Capture ALL technicians, labor items, parts, and charges listed across all pages.
        - Labor items should specifically capture technician names and their rates.
        - Vague charges are things like 'Service Fee', 'Truck Charge', 'Environmental Fee' without clear hourly or unit breakdown.
        - Ensure numerical values are floats.
        - Combine data from all pages into a single complete JSON output.
        """

        content_parts = [prompt]
        for fp in file_paths:
            with open(fp, "rb") as f:
                img_data = f.read()
            ext = os.path.splitext(fp)[1].lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            content_parts.append({"mime_type": mime, "data": img_data})

        response = self.model.generate_content(
            content_parts,
            generation_config={"response_mime_type": "application/json"}
        )

        try:
            data = json.loads(response.text)
            return InvoiceData(**data)
        except Exception as e:
            # Fallback or error handling
            print(f"Error parsing Gemini response: {e}")
            print(f"Raw response: {response.text}")
            raise
