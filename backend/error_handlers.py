from fastapi import HTTPException
from services.exceptions import OCRError, OCRUploadError, OCRProcessingError, OCRTimeoutError
from schemas import OCRErrorDetails

def handle_ocr_error(e: OCRError) -> OCRErrorDetails:
    """Convert OCR exceptions to structured error responses"""
    error_type = e.__class__.__name__
    return OCRErrorDetails(
        error_type=error_type,
        message=str(e),
        status_code=getattr(e, 'status_code', None),
        details=getattr(e, 'details', None)
    )

def raise_http_error(e: OCRError):
    """Convert OCR exceptions to appropriate HTTP errors"""
    error_details = handle_ocr_error(e)
    
    if isinstance(e, OCRUploadError):
        status_code = 400
    elif isinstance(e, OCRProcessingError):
        status_code = 422
    elif isinstance(e, OCRTimeoutError):
        status_code = 504
    else:
        status_code = 500
        
    raise HTTPException(
        status_code=status_code,
        detail={
            "error": error_details.dict()
        }
    )