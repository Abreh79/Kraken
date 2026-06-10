import os
from PIL import Image
from kraken_audit.extraction.utils.preprocess import preprocess_image

def test_preprocess():
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save('test_input.png')
    
    try:
        processed_path = preprocess_image('test_input.png')
        print(f"Processed image saved to: {processed_path}")
        if os.path.exists(processed_path):
            print("SUCCESS: Processed file exists.")
            os.remove(processed_path)
        else:
            print("FAILURE: Processed file not found.")
        os.remove('test_input.png')
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_preprocess()
