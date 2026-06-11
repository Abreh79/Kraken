import os
import tempfile
from .utils.preprocess import preprocess_image
from .extractor import GeminiExtractor
from .models import InvoiceData

def _convert_pdf_to_pngs(pdf_path: str) -> list:
    """Convert ALL pages of PDF to PNG images for Gemini processing using PyMuPDF."""
    import fitz
    doc = fitz.open(pdf_path)
    if doc.page_count == 0:
        raise ValueError(f"PDF has no pages: {pdf_path}")
    paths = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        pix = page.get_pixmap(dpi=200)
        tmp = tempfile.NamedTemporaryFile(suffix=f'_page{i+1}.png', delete=False)
        pix.save(tmp.name)
        paths.append(tmp.name)
    doc.close()
    return paths

def run_extraction(file_path: str, api_key: str = None) -> InvoiceData:
    """
    Main entry point for extraction.
    Handles multi-page PDFs, preprocessing, and calling the LLM.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    image_paths = []
    
    # Convert PDF pages → images
    if ext == '.pdf':
        image_paths = _convert_pdf_to_pngs(file_path)
    elif ext in ['.jpg', '.jpeg', '.png']:
        image_paths = [file_path]
    
    # Preprocess each image
    processed_paths = []
    for p in image_paths:
        processed = preprocess_image(p)
        if p != file_path:
            os.remove(p)  # remove raw conversion
        processed_paths.append(processed)
    
    # Extract — pass all page images to Gemini
    extractor = GeminiExtractor(api_key=api_key)
    invoice_data = extractor.extract(processed_paths)
    
    # Clean up temp files
    for p in processed_paths:
        if os.path.exists(p):
            os.remove(p)
        
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
