#!/usr/bin/env python3
"""
OCR Test Script
Test the OCR service directly with a sample image
"""
import asyncio
import sys
import os

async def test_ocr():
    try:
        # Import OCR service with proper path handling
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))
        sys.path.insert(0, os.path.dirname(__file__))
        
        from services.ocr_service import OCRService
        
        print("🔍 Testing OCR Service")
        print("=" * 40)
        
        ocr_service = OCRService()
        
        # Check if test image exists
        test_image_path = "storage/test_images/hibatest.jpg"
        
        if not os.path.exists(test_image_path):
            print(f"❌ Test image not found: {test_image_path}")
            # List available images
            if os.path.exists("storage"):
                print("\nAvailable files in storage:")
                for root, dirs, files in os.walk("storage"):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            print(f"  {os.path.join(root, file)}")
            return
        
        print(f"📄 Testing with image: {test_image_path}")
        
        # Run OCR
        extracted_text, confidence = await ocr_service.extract_text_from_image(test_image_path)
        
        print("\n📊 OCR Results:")
        print(f"  Extracted Text: '{extracted_text}'")
        print(f"  Confidence: {confidence}")
        print(f"  Text Length: {len(extracted_text) if extracted_text else 0}")
        print(f"  Is Empty: {extracted_text == '' if extracted_text is not None else 'None'}")
        
        if extracted_text and len(extracted_text.strip()) > 0:
            print("✅ OCR working correctly!")
        elif extracted_text == "":
            print("⚠️  OCR returned empty text - possible issues:")
            print("   - Image quality too poor")
            print("   - No text detected in image") 
            print("   - API key exhausted")
            print("   - OCR service configuration error")
        else:
            print("❌ OCR returned null/undefined")
            
    except Exception as e:
        print(f"❌ OCR test failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_ocr())