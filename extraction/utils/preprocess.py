from PIL import Image, ImageOps, ImageEnhance
import os

def preprocess_image(image_path: str) -> str:
    """
    Preprocesses the image for better OCR/LLM performance.
    Enhances contrast, handles rotation (auto), and saves a temporary processed version.
    """
    img = Image.open(image_path)
    
    # 1. Handle Orientation (if EXIF exists)
    img = ImageOps.exif_transpose(img)
    
    # 2. Convert to RGB if not already
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 3. Enhance Contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    
    # 4. Enhance Sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.2)
    
    # Save processed image
    base, ext = os.path.splitext(image_path)
    processed_path = f"{base}_processed.png"
    img.save(processed_path, format="PNG")
    
    return processed_path
