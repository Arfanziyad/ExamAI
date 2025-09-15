import os
import shutil
import uuid
import aiofiles
from typing import Optional, List, Dict, Any, cast
from fastapi import UploadFile, HTTPException
import logging
from PIL import Image  # Pillow package
import PyPDF2  # PyPDF2 package
from .ocr_service import OCRService
from .validation_service import OCRValidationService
from .exceptions import OCRError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        self.upload_dir = os.getenv("UPLOAD_DIR", "./storage")
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB default
        
        # Create directories
        self.question_papers_dir = os.path.join(self.upload_dir, "question_papers")
        self.model_answers_dir = os.path.join(self.upload_dir, "model_answers")
        self.submissions_dir = os.path.join(self.upload_dir, "submissions")
        self.processed_dir = os.path.join(self.upload_dir, "processed")
        
        self.ocr_service = OCRService()
        self.validation_service = OCRValidationService()
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        os.makedirs(self.question_papers_dir, exist_ok=True)
        os.makedirs(self.model_answers_dir, exist_ok=True)
        os.makedirs(self.submissions_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
    
    async def save_question_paper(self, file: UploadFile, file_type: str = "question") -> Dict[str, Any]:
        """
        Save uploaded question paper or model answer and extract text using OCR
        
        Returns:
            Dict with:
                file_path: path where file was saved
                extracted_text: text from OCR (optional)
                confidence: OCR confidence score (optional)
                validation_result: validation results (optional)
                
        Raises:
            OCRError: For OCR-related failures
            HTTPException: For file validation/saving errors
        """
        # Validate file
        self._validate_file(file, allowed_types=['application/pdf', 'image/jpeg', 'image/png'])
        
        # Generate unique filename
        file_extension = self._get_file_extension(file.filename)
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Choose directory based on file type
        base_dir = self.model_answers_dir if file_type == "model_answer" else self.question_papers_dir
        file_path = os.path.join(base_dir, unique_filename)
            
        try:
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        # Extract text using appropriate method
        extracted_text = None
        confidence = None
        validation_result = None

        try:
            if file.content_type == 'application/pdf':
                # For PDFs, try direct text extraction first
                extracted_text = self._extract_text_from_pdf(file_path)
                if not extracted_text or len(extracted_text.strip()) < 50:
                    # If PDF text extraction yields little text, try OCR
                    extracted_text, confidence = await self.ocr_service.extract_text_from_image(file_path)
            else:
                # For images, use OCR directly
                extracted_text, confidence = await self.ocr_service.extract_text_from_image(file_path)

            # Validate extracted text if available
            if extracted_text:
                validation_result = self.validation_service.validate_ocr_text(
                    extracted_text,
                    document_type=file_type
                )

                if not validation_result.is_valid:
                    logger.warning(f"OCR validation issues for {file_path}: {validation_result.issues}")

                if validation_result.warnings:
                    logger.info(f"OCR validation warnings for {file_path}: {validation_result.warnings}")

        except OCRError as e:
            # Log the error but don't fail the upload
            logger.warning(f"OCR processing failed for {file_path}: {str(e)}")
            # Re-raise OCRError to be handled by caller
            raise

        return {
            'file_path': file_path,
            'filename': unique_filename,
            'original_name': file.filename,
            'size': len(content),
            'content_type': file.content_type,
            'extracted_text': extracted_text,
            'confidence': confidence,
            'validation_result': {
                'is_valid': validation_result.is_valid,
                'issues': validation_result.issues,
                'warnings': validation_result.warnings,
                'metrics': validation_result.metrics
            } if validation_result else None
        }
    
    async def save_handwritten_submission(self, file: UploadFile, student_name: str, question_id: int) -> Dict[str, Any]:
        """Save handwritten answer submission"""
        try:
            # Validate image file
            self._validate_file(file, allowed_types=['image/jpeg', 'image/png', 'image/jpg'])
            
            # Generate unique filename with student info
            file_extension = self._get_file_extension(file.filename)
            safe_student_name = "".join(c for c in student_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            unique_filename = f"q{question_id}_{safe_student_name}_{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(self.submissions_dir, unique_filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Validate and process image
            image_info = self._process_image(file_path)
            
            return {
                'file_path': file_path,
                'filename': unique_filename,
                'original_name': file.filename,
                'size': len(content),
                'content_type': file.content_type,
                'image_info': image_info
            }
            
        except Exception as e:
            logger.error(f"Failed to save submission: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save submission: {str(e)}")
    
    def _validate_file(self, file: UploadFile, allowed_types: List[str]):
        """Validate uploaded file"""
        # Check filename first
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Check file size if available
        file_size = getattr(file, 'size', None)
        if file_size is not None and isinstance(file_size, (int, float)) and file_size > self.max_file_size:
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size: {self.max_file_size} bytes")
        
        # Check content type
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}")
    
    def _get_file_extension(self, filename: Optional[str]) -> str:
        """Get file extension from filename"""
        if not filename:
            return ".tmp"  # Default extension if none provided
        return os.path.splitext(filename)[1].lower() or ".tmp"  # Fallback to .tmp if no extension
    
    def _extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                
                return text.strip() if text.strip() else None
                
        except Exception as e:
            logger.warning(f"Failed to extract text from PDF: {str(e)}")
            return None
    
    def _process_image(self, file_path: str) -> Dict[str, Any]:
        """Process and validate image file"""
        try:
            with Image.open(file_path) as img:
                # Get image info
                image_info = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    img.save(file_path, 'JPEG', quality=85)
                    image_info['converted_to_rgb'] = True
                
                return image_info
                
        except Exception as e:
            logger.error(f"Failed to process image: {str(e)}")
            return {'error': str(e)}
    
    def get_file_url(self, file_path: str) -> str:
        """Get URL for accessing file"""
        # Return relative path for API access
        return file_path.replace(self.upload_dir, "/files").replace("\\", "/")
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a file"""
        try:
            if not os.path.exists(file_path):
                return None
                
            stat = os.stat(file_path)
            return {
                'path': file_path,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'exists': True
            }
        except Exception as e:
            logger.error(f"Failed to get file info: {str(e)}")
            return None