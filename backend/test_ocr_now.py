import asyncio
from services.ocr_service import OCRService
import os
from pathlib import Path

async def test_ocr():
    # Get path to test image
    test_image = Path(__file__).parent / "storage" / "test_images" / "hibatest.jpg"
    if not test_image.exists():
        print(f"Test image not found at: {test_image}")
        return

    print(f"Testing OCR with image: {test_image}")
    
    ocr = OCRService()
    text, confidence = await ocr.extract_text_from_image(str(test_image))
    
    print(f"\nExtracted Text:\n{text}")
    print(f"\nConfidence Score: {confidence}")

if __name__ == "__main__":
    asyncio.run(test_ocr())
