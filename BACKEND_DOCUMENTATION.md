# Backend System Documentation

## Overview

The ExamAI backend is a Flask-based API server that provides automatic evaluation of handwritten student answers using OCR (Optical Character Recognition) and AI-powered assessment. The system integrates multiple services to create a complete evaluation pipeline.

## System Architecture

### Database Schema

The system uses SQLite with SQLAlchemy ORM and consists of 5 main tables:

1. **QuestionPaper** - Stores question papers with questions and model answers
2. **Question** - Individual questions linked to question papers
3. **AnswerScheme** - Model answers and marking criteria for questions
4. **Submission** - Student submissions with handwritten answer images
5. **Evaluation** - AI-generated evaluations with scores and feedback

### Key Components

#### 1. Flask API Server (`flask_server.py`)
- **Port**: 5000
- **CORS Enabled**: For frontend communication
- **Main Endpoints**:
  - `GET /` - Health check
  - `GET /api/question-papers` - List all question papers
  - `POST /api/question-papers` - Create new question paper
  - `POST /api/questions/<id>/submissions` - Submit student answer (with automatic OCR + evaluation)
  - `GET /api/submissions` - Get all submissions with evaluations
  - `GET /api/submissions/<id>/evaluation` - Get specific evaluation
  - `POST /api/submissions/<id>/evaluate` - Manual re-evaluation

#### 2. OCR Service (`services/ocr_service.py`)
- **External API**: handwritingOCR.com
- **Functionality**: Converts handwritten text images to digital text
- **Process**:
  1. Upload image to OCR API
  2. Poll for processing completion
  3. Extract text and confidence score
- **Error Handling**: Comprehensive exception handling with fallback options

#### 3. Evaluation Service (`services/evaluator_service.py`)
- **Purpose**: Manages the evaluation workflow
- **Key Method**: `evaluate_submission_with_ocr()`
- **Process**:
  1. Fetch submission and associated question/model answer
  2. Use SubjectiveEvaluator for AI assessment
  3. Store evaluation results in database
- **Scoring**: Scales marks based on question's maximum marks

#### 4. Subjective Evaluator (`evaluators/subjective_evaluator.py`)
- **Type**: Lightweight, rule-based evaluator
- **Evaluation Criteria**:
  - **Semantic Score**: Understanding and meaning alignment
  - **Keyword Score**: Key term matching with model answer
  - **Structure Score**: Answer organization and completeness
  - **Comprehensiveness Score**: Coverage of model answer topics
- **Subject-Specific Weights**: Different weightings for science, math, humanities, programming, general
- **Output**: Similarity score (0-1), marks (0-10), detailed breakdown, AI feedback

## Current Workflow (How the System Actually Works)

**The system does NOT work as described in your question. Here's the actual workflow:**

### Phase 1: Question Paper Setup
1. **Manual Input**: Teachers create question papers through the API
2. **Storage**: Questions and model answers are stored as text in the database
3. **No OCR on Model Answers**: Model answers are entered as text, not converted from images

### Phase 2: Student Submission Process
1. **Image Upload**: Students submit handwritten answers as image files
2. **File Storage**: Images saved to `backend/storage/submissions/`
3. **Database Record**: Submission entry created with image path and metadata

### Phase 3: Automatic Processing (Triggered on Submission)
1. **OCR Processing**:
   - Image sent to handwritingOCR.com API
   - Text extracted from handwritten content
   - Confidence score calculated
   - Results stored in submission record

2. **AI Evaluation**:
   - Student text compared against model answer text
   - Multiple scoring dimensions calculated
   - Final marks and feedback generated
   - Evaluation record created and linked to submission

### Phase 4: Results Display
1. **API Access**: Frontend fetches evaluation results via REST API
2. **Formatted Output**: Scores, feedback, and detailed breakdowns displayed
3. **Manual Override**: Option for teachers to manually adjust scores

## Key Differences from Your Description

| Your Understanding | Actual Implementation |
|-------------------|----------------------|
| Question papers converted via OCR | Question papers entered as text directly |
| Model answers processed through OCR | Model answers stored as text in database |
| Two-step OCR process | Single OCR step only for student submissions |
| Sequential processing | Automatic processing triggered on submission |

## API Endpoints Reference

### Question Paper Management
```http
GET /api/question-papers
POST /api/question-papers
```

### Student Submissions
```http
POST /api/questions/{id}/submissions
# Multipart form data: file (image), student_name
# Automatically triggers OCR + Evaluation
```

### Evaluation Results
```http
GET /api/submissions
GET /api/submissions/{id}/evaluation
POST /api/submissions/{id}/evaluate  # Manual re-evaluation
```

## Data Flow

```
Student Image Upload
       ↓
File Storage + DB Record
       ↓
OCR Processing (handwritingOCR.com)
       ↓
Text Extraction + Confidence Score
       ↓
AI Evaluation (SubjectiveEvaluator)
       ↓
Score Calculation + Feedback Generation
       ↓
Database Storage (Evaluation table)
       ↓
Frontend Display (ViewResults)
```

## Evaluation Scoring System

### Score Components
- **Semantic Similarity** (35%): Meaning and understanding
- **Keyword Matching** (30%): Important terms present
- **Structure Quality** (20%): Organization and flow
- **Comprehensiveness** (15%): Topic coverage

### Subject-Specific Weighting
- **Science**: Higher keyword weight (35%)
- **Math**: Highest keyword focus (40%)
- **Humanities**: Emphasizes semantic understanding (40%)
- **Programming**: Technical accuracy priority (45% keywords)
- **General**: Balanced approach (default weights)

### Output Format
```json
{
  "similarity_score": 0.75,
  "marks_awarded": 7,
  "max_marks": 10,
  "detailed_scores": {
    "semantic": 82.5,
    "keyword": 70.0,
    "structure": 85.0,
    "comprehensiveness": 65.0
  },
  "ai_feedback": "Good understanding shown...",
  "evaluation_time": 1.23
}
```

## File Structure

```
backend/
├── flask_server.py           # Main API server
├── models.py                 # Database schema
├── database.py               # Database connection
├── services/
│   ├── ocr_service.py        # OCR integration
│   ├── evaluator_service.py  # Evaluation workflow
│   └── exceptions.py         # Custom exceptions
├── evaluators/
│   └── subjective_evaluator.py  # AI evaluation logic
└── storage/
    ├── submissions/          # Student answer images
    ├── question_papers/      # Question paper files (if any)
    └── model_answers/        # Model answer images (if any)
```

## Error Handling

The system implements comprehensive error handling:
- **OCR Failures**: Fallback mechanisms and retry logic
- **Evaluation Errors**: Default scoring with error messages
- **Database Issues**: Transaction rollbacks and cleanup
- **File Upload Problems**: Validation and secure storage

## Configuration

Key environment variables:
- `OCR_API_KEY`: API key for handwritingOCR.com service
- Database: SQLite file (`app.db`) in backend directory

## Current Status

✅ **Working Components**:
- Flask API server with all endpoints
- OCR integration with external service
- AI-based evaluation system
- Database schema and relationships
- File upload and storage
- Automatic processing pipeline

⚠️ **Limitations**:
- Lightweight evaluation (no advanced ML models)
- Basic similarity scoring
- Single OCR service dependency
- No real-time evaluation updates

This system provides a complete end-to-end workflow for automated assessment of handwritten student answers, from image upload through OCR processing to AI-powered evaluation and results display.