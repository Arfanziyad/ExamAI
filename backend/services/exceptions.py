from typing import Optional

class OCRError(Exception):
    """Base exception for OCR-related errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class OCRUploadError(OCRError):
    """Raised when document upload fails"""
    pass

class OCRProcessingError(OCRError):
    """Raised when OCR processing fails"""
    pass

class OCRTimeoutError(OCRError):
    """Raised when OCR processing times out"""
    pass

class OCRValidationError(OCRError):
    """Raised when OCR result validation fails"""
    pass