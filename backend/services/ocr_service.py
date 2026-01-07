import os
import aiohttp
import aiofiles
import asyncio
from typing import Tuple, Dict, Any, Optional, List
from dotenv import load_dotenv
from .exceptions import OCRError, OCRUploadError, OCRProcessingError, OCRTimeoutError
from .answer_sequence_service import analyze_answer_sequence

load_dotenv()

class OCRService:
    def __init__(self):
        self.api_key = os.getenv('OCR_API_KEY', '1942|JhUikWLXVsvpVILtp6O802ShOtv8dhQQ7NZy5n6Aed2836fe')
        # Use environment variable for base URL, fallback to v3 endpoint
        self.base_url = os.getenv('OCR_API_URL', 'https://www.handwritingocr.com/api/v3')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }

    async def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from image using handwritingOCR.com API
        Returns: Tuple of (extracted_text, confidence_score)
        Raises:
            OCRUploadError: When document upload fails
            OCRProcessingError: When OCR processing fails
            OCRTimeoutError: When OCR processing times out
            OCRError: For other OCR-related errors
        """
        if not os.path.exists(image_path):
            raise OCRError(f"Image file not found: {image_path}")

        try:
            # 1. Upload document
            document_id = await self._upload_document(image_path)
            if not document_id:
                raise OCRUploadError("Failed to upload document for OCR processing")

            # 2. Poll until processing is complete
            result = await self._get_result(document_id)
            if not result:
                raise OCRProcessingError("OCR processing failed or timed out")

            # 3. Extract text from results
            if not result.get('results'):
                raise OCRProcessingError("No results found in OCR response", 
                                       details={'document_id': document_id})

            # Combine text from all pages
            text = ' '.join(
                page['transcript'] 
                for page in result['results']
            )

            if not text.strip():
                raise OCRProcessingError("OCR returned empty text", 
                                       details={'document_id': document_id})

            # Calculate confidence based on result metadata if available
            confidence = result.get('metadata', {}).get('confidence', 0.9)
            return (text, confidence)

        except aiohttp.ClientError as e:
            raise OCRError(f"API communication error: {str(e)}") from e
        except asyncio.TimeoutError as e:
            raise OCRTimeoutError("OCR processing timed out") from e
        except Exception as e:
            if isinstance(e, OCRError):
                raise
            raise OCRError(f"Unexpected error during OCR: {str(e)}") from e

    async def _upload_document(self, image_path: str) -> str:
        """
        Upload document to API and return document ID
        
        Raises:
            OCRUploadError: When document upload fails
            OCRError: For other upload-related errors
        """
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('action', 'transcribe')
                
                async with aiofiles.open(image_path, 'rb') as f:
                    file_data = await f.read()
                    data.add_field(
                        'file',
                        file_data,
                        filename=os.path.basename(image_path)
                    )

                async with session.post(
                    f'{self.base_url}/documents',
                    headers=self.headers,
                    data=data
                ) as response:
                    response_text = await response.text()
                    
                    # Debug logging
                    print(f"OCR Upload Debug:")
                    print(f"  URL: {self.base_url}/documents")
                    print(f"  Status: {response.status}")
                    print(f"  Headers sent: {self.headers}")
                    print(f"  Response: {response_text[:200]}...")
                    
                    if response.status == 201:
                        result = await response.json()
                        doc_id = result.get('id')
                        if not doc_id:
                            raise OCRUploadError("No document ID in upload response")
                        return doc_id
                    
                    error_details = {
                        'status_code': response.status,
                        'response': response_text
                    }
                    raise OCRUploadError(
                        f"Upload failed with status {response.status}",
                        status_code=response.status,
                        details=error_details
                    )

        except aiohttp.ClientError as e:
            raise OCRError(f"API communication error during upload: {str(e)}") from e
        except OCRError:
            raise
        except Exception as e:
            raise OCRError(f"Unexpected error during upload: {str(e)}") from e

    async def _get_result(self, document_id: str) -> Dict[str, Any]:
        """
        Poll for results until document is processed
        
        Raises:
            OCRProcessingError: When processing fails
            OCRTimeoutError: When max polling attempts reached
            OCRError: For other processing-related errors
        """
        try:
            async with aiohttp.ClientSession() as session:
                max_attempts = 10
                attempt = 0
                backoff_factor = 2

                while attempt < max_attempts:
                    try:
                        async with session.get(
                            f'{self.base_url}/documents/{document_id}',
                            headers=self.headers
                        ) as response:
                            response_text = await response.text()
                            
                            if response.status == 200:
                                result = await response.json()
                                status = result.get('status')
                                
                                if status == 'processed':
                                    return result
                                elif status == 'failed':
                                    error_details = {
                                        'document_id': document_id,
                                        'status': status,
                                        'error': result.get('error')
                                    }
                                    raise OCRProcessingError(
                                        "Document processing failed",
                                        details=error_details
                                    )
                                elif status == 'processing':
                                    # Continue polling
                                    pass
                                else:
                                    error_details = {
                                        'document_id': document_id,
                                        'status': status
                                    }
                                    raise OCRProcessingError(
                                        f"Unexpected document status: {status}",
                                        details=error_details
                                    )
                            else:
                                error_details = {
                                    'status_code': response.status,
                                    'response': response_text
                                }
                                raise OCRError(
                                    f"API error while polling: {response.status}",
                                    status_code=response.status,
                                    details=error_details
                                )

                    except aiohttp.ClientError as e:
                        # For connection errors, retry with backoff
                        if attempt == max_attempts - 1:
                            raise OCRError(f"API communication error while polling: {str(e)}") from e

                    # Wait with exponential backoff
                    await asyncio.sleep(backoff_factor ** attempt)
                    attempt += 1

                raise OCRTimeoutError(
                    "Max polling attempts reached",
                    details={'document_id': document_id, 'attempts': max_attempts}
                )

        except OCRError:
            raise
        except Exception as e:
            raise OCRError(f"Unexpected error while polling: {str(e)}") from e

    def _mock_extract_text(self) -> Tuple[str, float]:
        """Fallback mock implementation"""
        return (
            "This is mock extracted text for testing purposes. "
            "The real OCR service is either not available or encountered an error.",
            0.85
        )

    async def extract_and_analyze_sequence(
        self, 
        image_path: str, 
        expected_questions: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract text from image and analyze answer sequence
        
        Args:
            image_path: Path to the image file
            expected_questions: List of expected question details for sequence analysis
            
        Returns:
            Dictionary containing:
            - extracted_text: Raw OCR text
            - ocr_confidence: OCR confidence score
            - sequence_analysis: Answer sequence analysis results
        """
        try:
            # Extract text using OCR
            extracted_text, ocr_confidence = await self.extract_text_from_image(image_path)
            
            # Analyze answer sequence if we have expected questions
            sequence_analysis = None
            if expected_questions and extracted_text.strip():
                sequence_analysis = analyze_answer_sequence(extracted_text, expected_questions)
            
            return {
                'extracted_text': extracted_text,
                'ocr_confidence': ocr_confidence,
                'sequence_analysis': sequence_analysis,
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'extracted_text': '',
                'ocr_confidence': 0.0,
                'sequence_analysis': None,
                'status': 'error',
                'error': str(e)
            }
