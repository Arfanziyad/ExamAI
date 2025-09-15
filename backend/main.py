from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import update, inspect
from sqlalchemy import text
from typing import List, Optional, Dict, Any, Union
import os
import logging
import json
from datetime import datetime

def update_model_instance(instance, **kwargs):
    """Helper function to update SQLAlchemy model instance attributes"""
    for key, value in kwargs.items():
        setattr(instance, key, value)
    return instance

def get_model_attr(instance, attr: str, default: Any = None) -> Any:
    """Helper function to safely get SQLAlchemy model attributes"""
    mapper = inspect(instance).mapper
    if attr in mapper.columns.keys():
        value = getattr(instance, attr)
        return value.scalar() if hasattr(value, 'scalar') else value
    return default

# Import local modules
from database import get_db, create_tables
from models import QuestionPaper, Question, AnswerScheme, Submission, Evaluation
from schemas import (
    QuestionPaperCreate, QuestionPaperResponse, QuestionCreate, QuestionResponse,
    AnswerSchemeCreate, AnswerSchemeResponse, SubmissionCreate, SubmissionResponse,
    EvaluationResponse, ManualEvaluationUpdate, QuestionPaperWithQuestions,
    PerformanceAnalytics, StudentPerformance, OCRVerificationRequest, OCRResult
)
from services.file_service import FileService
from services.ocr_service import OCRService
from services.evaluator_service import EvaluatorService
from services.analytics_service import AnalyticsService
from services.exceptions import OCRError
from error_handlers import handle_ocr_error, raise_http_error

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Subjective Answer Evaluator",
    description="Automated evaluation of handwritten subjective answers using AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
file_service = FileService()
ocr_service = OCRService()
evaluator_service = EvaluatorService()

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    logger.info("Database tables created")

# Mount static files
app.mount("/files", StaticFiles(directory="./storage"), name="files")

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "AI Subjective Answer Evaluator API", "status": "running"}

# ==================== QUESTION PAPER ENDPOINTS ====================

@app.post("/api/question-papers", response_model=QuestionPaperResponse)
async def create_question_paper(
    title: str = Form(...),
    subject: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    answer_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a question paper and model answer"""
    try:
        # Process question paper file
        try:
            question_info = await file_service.save_question_paper(file, file_type="question")
            question_ocr = OCRResult(
                extracted_text=question_info.get('extracted_text'),
                confidence=question_info.get('confidence'),
                validation_result=None,
                error=None
            )
        except OCRError as e:
            logger.warning(f"OCR failed for question file: {str(e)}")
            question_ocr = OCRResult(
                extracted_text=None,
                confidence=None,
                validation_result=None,
                error=handle_ocr_error(e)
            )

        # Process model answer file
        try:
            answer_info = await file_service.save_question_paper(answer_file, file_type="model_answer")
            answer_ocr = OCRResult(
                extracted_text=answer_info.get('extracted_text'),
                confidence=answer_info.get('confidence'),
                validation_result=None,
                error=None
            )
        except OCRError as e:
            logger.warning(f"OCR failed for answer file: {str(e)}")
            answer_ocr = OCRResult(
                extracted_text=None,
                confidence=None,
                validation_result=None,
                error=handle_ocr_error(e)
            )

        # Validate results
        if (not question_info.get('file_path') or not answer_info.get('file_path')):
            raise HTTPException(
                status_code=400,
                detail="Failed to save uploaded files"
            )

        # Create question paper record
        question_paper = QuestionPaper(
            title=title,
            subject=subject,
            description=description,
            file_path=question_info['file_path'],
            answer_file_path=answer_info['file_path'],
            question_text=text(question_ocr.extracted_text) if question_ocr.extracted_text else None,
            answer_text=text(answer_ocr.extracted_text) if answer_ocr.extracted_text else None,
            question_ocr=question_ocr.dict(),
            answer_ocr=answer_ocr.dict()
        )
        
        db.add(question_paper)
        db.commit()
        db.refresh(question_paper)
        
        logger.info(f"Question paper created: {question_paper.id}")
        return question_paper
        
    except OCRError as e:
        db.rollback()
        logger.error(f"OCR error while creating question paper: {str(e)}")
        raise_http_error(e)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create question paper: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/question-papers", response_model=List[QuestionPaperResponse])
async def get_question_papers(db: Session = Depends(get_db)):
    """Get all question papers"""
    return db.query(QuestionPaper).all()

@app.get("/api/question-papers/{paper_id}", response_model=QuestionPaperWithQuestions)
async def get_question_paper(paper_id: int, db: Session = Depends(get_db)):
    """Get a specific question paper with questions"""
    paper = db.query(QuestionPaper).filter(QuestionPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Question paper not found")
    return paper

# ==================== QUESTION ENDPOINTS ====================

@app.post("/api/question-papers/{paper_id}/questions", response_model=QuestionResponse)
async def create_question(
    paper_id: int,
    question_data: QuestionCreate,
    db: Session = Depends(get_db)
):
    """Create a new question for a question paper"""
    # Check if paper exists
    paper = db.query(QuestionPaper).filter(QuestionPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Question paper not found")
    
    question = Question(
        question_paper_id=paper_id,
        question_text=question_data.question_text,
        question_number=question_data.question_number,
        max_marks=question_data.max_marks,
        subject_area=question_data.subject_area
    )
    
    db.add(question)
    db.commit()
    db.refresh(question)
    
    return question

@app.get("/api/questions", response_model=List[QuestionResponse])
async def get_all_questions(db: Session = Depends(get_db)):
    """Get all questions"""
    return db.query(Question).all()

@app.get("/api/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: Session = Depends(get_db)):
    """Get a specific question"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@app.put("/api/question-papers/{paper_id}/ocr-verify")
async def verify_ocr_text(
    paper_id: int,
    verification: OCRVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify and update OCR extracted text"""
    paper = db.query(QuestionPaper).filter(QuestionPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Question paper not found")
    
    try:
        if verification.type == "question":
            setattr(paper, 'question_text', text(verification.corrected_text))
        elif verification.type == "model_answer":
            setattr(paper, 'answer_text', text(verification.corrected_text))
        else:
            raise HTTPException(status_code=400, detail="Invalid type. Must be 'question' or 'model_answer'")
        
        db.commit()
        return {"message": "OCR text updated successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update OCR text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    try:
        db.commit()
        logger.info(f"OCR text verified for paper {paper_id} ({verification.type})")
        return {"status": "success", "message": "OCR text updated successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update OCR text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ANSWER SCHEME ENDPOINTS ====================

@app.post("/api/questions/{question_id}/answer-scheme", response_model=AnswerSchemeResponse)
async def create_answer_scheme(
    question_id: int,
    scheme_data: AnswerSchemeCreate,
    db: Session = Depends(get_db)
):
    """Create answer scheme for a question"""
    # Check if question exists
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if answer scheme already exists
    existing_scheme = db.query(AnswerScheme).filter(AnswerScheme.question_id == question_id).first()
    if existing_scheme:
        raise HTTPException(status_code=400, detail="Answer scheme already exists for this question")
    
    answer_scheme = AnswerScheme(
        question_id=question_id,
        model_answer=scheme_data.model_answer,
        key_points=scheme_data.key_points,
        marking_criteria=scheme_data.marking_criteria,
        sample_answers=scheme_data.sample_answers
    )
    
    db.add(answer_scheme)
    db.commit()
    db.refresh(answer_scheme)
    
    return answer_scheme

@app.get("/api/questions/{question_id}/answer-scheme", response_model=AnswerSchemeResponse)
async def get_answer_scheme(question_id: int, db: Session = Depends(get_db)):
    """Get answer scheme for a question"""
    scheme = db.query(AnswerScheme).filter(AnswerScheme.question_id == question_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Answer scheme not found")
    return scheme

@app.put("/api/questions/{question_id}/answer-scheme", response_model=AnswerSchemeResponse)
async def update_answer_scheme(
    question_id: int,
    scheme_data: AnswerSchemeCreate,
    db: Session = Depends(get_db)
):
    """Update answer scheme for a question"""
    scheme = db.query(AnswerScheme).filter(AnswerScheme.question_id == question_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Answer scheme not found")
    
    update_model_instance(
        scheme,
        model_answer=scheme_data.model_answer,
        key_points=scheme_data.key_points,
        marking_criteria=scheme_data.marking_criteria,
        sample_answers=scheme_data.sample_answers
    )
    
    db.commit()
    db.refresh(scheme)
    
    return scheme

# ==================== SUBMISSION ENDPOINTS ====================

@app.post("/api/questions/{question_id}/submissions", response_model=SubmissionResponse)
async def submit_answer(
    question_id: int,
    student_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Submit a handwritten answer"""
    try:
        # Check if question exists
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Save handwritten image
        file_info = await file_service.save_handwritten_submission(file, student_name, question_id)
        
        # Create submission record
        submission = Submission(
            question_id=question_id,
            student_name=student_name,
            handwriting_image_path=file_info['file_path']
        )
        
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        # Process OCR in background
        try:
            extracted_text, confidence = await ocr_service.extract_text_from_image(file_info['file_path'])
            update_model_instance(
                submission,
                extracted_text=extracted_text,
                ocr_confidence=confidence
            )
            db.commit()
            
            logger.info(f"OCR completed for submission {submission.id}")
        except Exception as e:
            logger.error(f"OCR failed for submission {submission.id}: {str(e)}")
        
        return submission
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create submission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(submission_id: int, db: Session = Depends(get_db)):
    """Get a specific submission"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

@app.get("/api/questions/{question_id}/submissions", response_model=List[SubmissionResponse])
async def get_question_submissions(question_id: int, db: Session = Depends(get_db)):
    """Get all submissions for a question"""
    return db.query(Submission).filter(Submission.question_id == question_id).all()

# ==================== EVALUATION ENDPOINTS ====================

@app.post("/api/submissions/{submission_id}/evaluate", response_model=EvaluationResponse)
async def evaluate_submission(submission_id: int, db: Session = Depends(get_db)):
    """Evaluate a submission using AI"""
    try:
        # Get submission
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Check if already evaluated
        existing_eval = db.query(Evaluation).filter(Evaluation.submission_id == submission_id).first()
        if existing_eval:
            return existing_eval
        
        # Get answer scheme
        answer_scheme = db.query(AnswerScheme).filter(
            AnswerScheme.question_id == submission.question_id
        ).first()
        
        if not answer_scheme:
            raise HTTPException(status_code=404, detail="Answer scheme not found for this question")
        
        # Check if OCR text is available
        extracted_text = get_model_attr(submission, 'extracted_text')
        if not extracted_text:
            raise HTTPException(status_code=400, detail="OCR text not available. Please wait for processing.")
        
        # Evaluate using AI
        evaluation_result = await evaluator_service.evaluate_answer(
            question_text=get_model_attr(submission.question, 'question_text'),
            student_answer=extracted_text,
            model_answer=get_model_attr(answer_scheme, 'model_answer'),
            subject_area=get_model_attr(submission.question, 'subject_area'),
            max_marks=get_model_attr(submission.question, 'max_marks')
        )
        
        # Create evaluation record
        evaluation = Evaluation(
            submission_id=submission_id,
            similarity_score=evaluation_result['similarity_score'],
            marks_awarded=evaluation_result['marks_awarded'],
            max_marks=evaluation_result['max_marks'],
            detailed_scores=evaluation_result['detailed_scores'],
            ai_feedback=evaluation_result['ai_feedback'],
            evaluation_time=evaluation_result['evaluation_time']
        )
        
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        logger.info(f"Evaluation completed for submission {submission_id}")
        return evaluation
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to evaluate submission {submission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/submissions/{submission_id}/evaluation", response_model=EvaluationResponse)
async def get_evaluation(submission_id: int, db: Session = Depends(get_db)):
    """Get evaluation for a submission"""
    evaluation = db.query(Evaluation).filter(Evaluation.submission_id == submission_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation

@app.put("/api/evaluations/{evaluation_id}/override", response_model=EvaluationResponse)
async def override_evaluation(
    evaluation_id: int,
    override_data: ManualEvaluationUpdate,
    db: Session = Depends(get_db)
):
    """Manually override AI evaluation"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    update_model_instance(
        evaluation,
        manual_marks=override_data.manual_marks,
        manual_feedback=override_data.manual_feedback,
        is_manually_overridden=1,
        updated_at=datetime.utcnow()
    )
    
    db.commit()
    db.refresh(evaluation)
    
    return evaluation

# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/api/analytics/performance", response_model=Dict[str, Any])
async def get_performance_analytics(
    question_paper_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get overall performance analytics"""
    return AnalyticsService.get_performance_analytics(db, question_paper_id)

@app.get("/api/analytics/student/{student_name}", response_model=Dict[str, Any])
async def get_student_performance(student_name: str, db: Session = Depends(get_db)):
    """Get performance analytics for a specific student"""
    return AnalyticsService.get_student_performance(db, student_name)

@app.get("/api/analytics/question/{question_id}", response_model=Dict[str, Any])
async def get_question_analytics(question_id: int, db: Session = Depends(get_db)):
    """Get analytics for a specific question"""
    return AnalyticsService.get_question_analytics(db, question_id)

# ==================== UTILITY ENDPOINTS ====================

@app.get("/api/subjects")
async def get_available_subjects():
    """Get list of available subjects"""
    return [
        {"value": "general", "label": "General"},
        {"value": "science", "label": "Science"},
        {"value": "math", "label": "Mathematics"},
        {"value": "humanities", "label": "Humanities"},
        {"value": "programming", "label": "Programming"}
    ]

@app.get("/api/evaluation-criteria/{subject_area}")
async def get_evaluation_criteria(subject_area: str):
    """Get evaluation criteria for a subject area"""
    return evaluator_service.get_evaluation_criteria(subject_area)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)