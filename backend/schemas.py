from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Question Paper Schemas
class OCRVerificationRequest(BaseModel):
    type: str  # 'question' or 'model_answer'
    corrected_text: str

class QuestionPaperCreate(BaseModel):
    title: str
    subject: str
    description: Optional[str] = None

class OCRValidationResult(BaseModel):
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]

class OCRErrorDetails(BaseModel):
    error_type: str  # e.g. "OCRUploadError", "OCRProcessingError"
    message: str
    status_code: Optional[int]
    details: Optional[Dict[str, Any]]

class OCRResult(BaseModel):
    extracted_text: Optional[str]
    confidence: Optional[float]
    validation_result: Optional[OCRValidationResult]
    error: Optional[OCRErrorDetails]

class QuestionPaperResponse(BaseModel):
    id: int
    title: str
    subject: str
    description: Optional[str]
    question_text: str
    answer_text: str
    file_path: Optional[str]
    answer_file_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Question Schemas
class QuestionCreate(BaseModel):
    question_text: str
    question_number: int
    max_marks: int = 10
    subject_area: str = "general"

class QuestionResponse(BaseModel):
    id: int
    question_paper_id: int
    question_text: str
    question_number: int
    max_marks: int
    subject_area: str
    
    class Config:
        from_attributes = True

# Answer Scheme Schemas
class AnswerSchemeCreate(BaseModel):
    model_answer: str
    key_points: Optional[List[str]] = []
    marking_criteria: Optional[Dict[str, Any]] = {}
    sample_answers: Optional[Dict[str, List[str]]] = {}

class AnswerSchemeResponse(BaseModel):
    id: int
    question_id: int
    model_answer: str
    key_points: Optional[List[str]]
    marking_criteria: Optional[Dict[str, Any]]
    sample_answers: Optional[Dict[str, List[str]]]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Submission Schemas
class SubmissionCreate(BaseModel):
    student_name: str

class SubmissionResponse(BaseModel):
    id: int
    question_id: int
    student_name: str
    handwriting_image_path: str
    extracted_text: Optional[str]
    ocr_confidence: Optional[float]
    submitted_at: datetime
    
    class Config:
        from_attributes = True

# Evaluation Schemas
class EvaluationResponse(BaseModel):
    id: int
    submission_id: int
    similarity_score: float
    marks_awarded: int
    max_marks: int
    detailed_scores: Dict[str, Any]
    ai_feedback: str
    manual_marks: Optional[int]
    manual_feedback: Optional[str]
    is_manually_overridden: bool
    evaluation_time: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class ManualEvaluationUpdate(BaseModel):
    manual_marks: int
    manual_feedback: str

# Combined Response Schemas
class QuestionWithAnswerScheme(BaseModel):
    id: int
    question_paper_id: int
    question_text: str
    question_number: int
    max_marks: int
    subject_area: str
    answer_scheme: Optional[AnswerSchemeResponse]
    
    class Config:
        from_attributes = True

class SubmissionWithEvaluation(BaseModel):
    id: int
    question_id: int
    student_name: str
    handwriting_image_path: str
    extracted_text: Optional[str]
    ocr_confidence: Optional[float]
    submitted_at: datetime
    evaluation: Optional[EvaluationResponse]
    
    class Config:
        from_attributes = True

class QuestionPaperWithQuestions(BaseModel):
    id: int
    title: str
    subject: str
    description: Optional[str]
    created_at: datetime
    questions: List[QuestionWithAnswerScheme]
    
    class Config:
        from_attributes = True

# Analytics Schemas
class PerformanceAnalytics(BaseModel):
    total_submissions: int
    average_score: float
    score_distribution: Dict[str, int]
    common_mistakes: List[str]
    top_performers: List[Dict[str, Any]]

class StudentPerformance(BaseModel):
    student_name: str
    submissions: List[SubmissionWithEvaluation]
    average_score: float
    improvement_trend: List[Dict[str, Any]]