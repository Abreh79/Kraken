import os
import tempfile
from .utils.preprocess import preprocess_image
from .extractor import GeminiExtractor
from .models import InvoiceData

def _convert_pdf_to_png(pdf_path: str) -> str:
    """Convert first page of PDF to PNG for Gemini processing using PyMuPDF."""
    import fitz
    doc = fitz.open(pdf_path)
    if doc.page_count == 0:
        raise ValueError(f"PDF has no pages: {pdf_path}")
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=200)
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    pix.save(tmp.name)
    doc.close()
    return tmp.name

def run_extraction(file_path: str, api_key: str = None) -> InvoiceData:
    """
    Main entry point for extraction.
    Handles preprocessing and calling the LLM.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    needs_cleanup = False
    
    # Convert PDF to image first
    if ext == '.pdf':
        file_path = _convert_pdf_to_png(file_path)
        needs_cleanup = True
        ext = '.png'
    
    # Preprocess image for better OCR
    if ext in ['.jpg', '.jpeg', '.png']:
        processed_path = preprocess_image(file_path)
        if needs_cleanup:
            os.remove(file_path)  # remove the raw conversion
        needs_cleanup = True
        file_path = processed_path
    
    # Extract
    extractor = GeminiExtractor(api_key=api_key)
    invoice_data = extractor.extract(file_path)
    
    # Clean up temp files
    if needs_cleanup and os.path.exists(file_path):
        os.remove(file_path)
        
    return invoice_data

if __name__ == "__main__":
    # Example usage
    import sys
    import json
    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            result = run_extraction(path)
            print(result.model_dump_json(indent=2))
        except Exception as e:
            print(f"Extraction failed: {e}")
    else:
        print("Usage: python -m kraken_audit.extraction.engine <file_path>")
