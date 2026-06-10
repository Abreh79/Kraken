import os
from .utils.preprocess import preprocess_image
from .extractor import GeminiExtractor
from .models import InvoiceData

def run_extraction(file_path: str, api_key: str = None) -> InvoiceData:
    """
    Main entry point for extraction.
    Handles preprocessing and calling the LLM.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # 1. Preprocess
    # If it's a PDF, we might need to convert to image first, 
    # but Gemini handles PDFs. However, preprocessing helps for photos.
    # For now, let's assume image input or handle PDF separately.
    
    ext = os.path.splitext(file_path)[1].lower()
    processed_path = file_path
    
    if ext in ['.jpg', '.jpeg', '.png']:
        processed_path = preprocess_image(file_path)
    
    # 2. Extract
    extractor = GeminiExtractor(api_key=api_key)
    invoice_data = extractor.extract(processed_path)
    
    # Clean up processed image if it was created
    if processed_path != file_path:
        os.remove(processed_path)
        
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
