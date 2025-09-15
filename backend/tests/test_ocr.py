import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from services.ocr_service import OCRService

async def test_ocr():
    # Initialize OCR service
    ocr_service = OCRService()
    
    # Get test image path
    test_dir = Path("storage/test_images")
    if not test_dir.exists():
        test_dir.mkdir(parents=True)
    
    # Test with sample image
    test_image_path = test_dir / "test_handwriting.jpg"
    
    if not test_image_path.exists():
        print(f"Please add a test image at: {test_image_path}")
        return
    
    try:
        # Test OCR
        text, confidence = await ocr_service.extract_text_from_image(str(test_image_path))
        
        print("OCR Test Results:")
        print("-" * 50)
        print(f"Extracted Text: {text}")
        print(f"Confidence Score: {confidence}")
        print("-" * 50)
        
    except Exception as e:
        print(f"Error testing OCR: {e}")

if __name__ == "__main__":
    asyncio.run(test_ocr())
