import os
import asyncio
from typing import Tuple
import random

class MockOCRService:
    """
    Mock OCR service for testing when API limits are exceeded
    Returns realistic sample OCR results
    """
    
    def __init__(self):
        self.sample_texts = [
            "Photosynthesis is the process by which plants convert light energy into chemical energy.",
            "The water cycle includes evaporation, condensation, precipitation, and collection.",
            "Newton's first law states that an object at rest stays at rest unless acted upon by an external force.",
            "The mitochondria is the powerhouse of the cell because it produces ATP through cellular respiration.",
            "To solve 2x + 5 = 13: subtract 5 from both sides to get 2x = 8, then divide by 2 to get x = 4.",
            "Shakespeare's Romeo and Juliet explores themes of love, fate, and family conflict.",
            "The French Revolution began in 1789 and led to significant political and social changes.",
            "DNA carries genetic information and is composed of four nucleotide bases: A, T, G, and C."
        ]
    
    async def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """
        Mock OCR extraction - returns a sample response
        """
        if not os.path.exists(image_path):
            raise Exception(f"Image file not found: {image_path}")
        
        # Simulate processing delay
        await asyncio.sleep(1)
        
        # Return a random sample text with high confidence
        mock_text = random.choice(self.sample_texts)
        mock_confidence = round(random.uniform(0.87, 0.94), 2)
        
        print(f"MOCK OCR: Processed {os.path.basename(image_path)}")
        print(f"MOCK OCR: Text: {mock_text[:50]}...")
        print(f"MOCK OCR: Confidence: {mock_confidence}")
        
        return (mock_text, mock_confidence)