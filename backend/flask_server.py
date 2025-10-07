from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_db, create_tables
from models import QuestionPaper, Question, AnswerScheme, Submission, Evaluation
from evaluators.subjective_evaluator import SubjectiveEvaluator
from evaluators.coding_evaluator import CodingEvaluator
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "running"})

@app.route("/api/question-papers", methods=["GET"])
def get_question_papers():
    try:
        db = next(get_db())
        try:
            papers = db.query(QuestionPaper).all()
            result = []
            for paper in papers:
                created_at = paper.created_at.isoformat() if hasattr(paper, 'created_at') and paper.created_at is not None else None
                
                # Get the associated Question ID
                question = db.query(Question).filter(Question.question_paper_id == paper.id).first()
                question_id = question.id if question else None
                
                result.append({
                    "id": paper.id,
                    "question_id": question_id,  # Include the actual question ID for submissions
                    "title": paper.title,
                    "subject": paper.subject,
                    "description": paper.description,
                    "question_text": paper.question_text,
                    "answer_text": paper.answer_text,
                    "created_at": created_at
                })
            return jsonify(result)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/question-papers", methods=["POST"])
def create_question_paper():
    try:
        # Get form data or JSON data
        data = request.get_json() if request.is_json else request.form
        
        # Get and validate fields
        title = str(data.get("title", "")).strip()
        subject = str(data.get("subject", "")).strip()
        description = str(data.get("description", "")).strip()
        question_text = str(data.get("question_text", "")).strip()
        answer_text = str(data.get("answer_text", "")).strip()

        # Check required fields
        required_fields = {
            "title": title,
            "subject": subject,
            "question_text": question_text,
            "answer_text": answer_text
        }
        missing_fields = [field for field, value in required_fields.items() if not value]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Get database session
        db = next(get_db())
        try:
            # Create question paper
            question_paper = QuestionPaper(
                title=title,
                subject=subject,
                description=description,
                question_text=question_text,
                answer_text=answer_text
            )
            
            # Save to database
            db.add(question_paper)
            db.commit()
            db.refresh(question_paper)

            # Automatically create a Question record for this QuestionPaper
            try:
                question = Question(
                    question_paper_id=question_paper.id,
                    question_text=question_text,
                    question_number=1,
                    max_marks=10,  # Default max marks
                    subject_area=subject.lower() if subject else 'general'
                )
                db.add(question)
                db.commit()
                db.refresh(question)
                
                # Create an AnswerScheme for the question
                answer_scheme = AnswerScheme(
                    question_id=question.id,
                    model_answer=answer_text,
                    key_points=[],  # Can be populated later
                    marking_criteria={},  # Can be populated later
                    sample_answers=[]  # Can be populated later
                )
                db.add(answer_scheme)
                db.commit()
                
                logger.info(f"Created QuestionPaper {question_paper.id}, Question {question.id}, and AnswerScheme {answer_scheme.id}")
                question_id = question.id
            except Exception as q_error:
                logger.error(f"Failed to create Question/AnswerScheme: {str(q_error)}")
                question_id = None

            # Convert to dict for JSON response
            created_at = None
            if hasattr(question_paper, 'created_at'):
                dt = question_paper.created_at
                if dt is not None:
                    created_at = dt.isoformat()

            response = {
                "id": question_paper.id,
                "question_id": question_id,  # Include the question ID for frontend use
                "title": question_paper.title,
                "subject": question_paper.subject,
                "description": question_paper.description,
                "question_text": question_paper.question_text,
                "answer_text": question_paper.answer_text,
                "created_at": created_at
            }
            
            return jsonify(response), 201

        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": "Database error occurred"}), 500
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/question-papers/multiple", methods=["POST"])
def create_question_paper_multiple():
    """Create a question paper with multiple questions and answers"""
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Get and validate basic fields
        title = str(data.get("title", "")).strip()
        subject = str(data.get("subject", "")).strip()
        description = str(data.get("description", "")).strip()
        questions_data = data.get("questions", [])

        # Check required fields
        if not title:
            return jsonify({"error": "Title is required"}), 400
        if not subject:
            return jsonify({"error": "Subject is required"}), 400
        if not questions_data or len(questions_data) == 0:
            return jsonify({"error": "At least one question is required"}), 400

        # Validate questions
        for i, q_data in enumerate(questions_data):
            if not q_data.get("question_text", "").strip():
                return jsonify({"error": f"Question text is required for question {i+1}"}), 400
            if not q_data.get("answer_text", "").strip():
                return jsonify({"error": f"Answer text is required for question {i+1}"}), 400

        # Get database session
        db = next(get_db())
        try:
            # Calculate total marks for the question paper
            total_marks = sum(q_data.get("max_marks", 10) for q_data in questions_data)
            
            # Create question paper
            # For backward compatibility, combine all questions into question_text and answer_text
            combined_question_text = "\n\n".join([
                f"Question {i+1}: {q['question_text']}" 
                for i, q in enumerate(questions_data)
            ])
            combined_answer_text = "\n\n".join([
                f"Answer {i+1}: {q['answer_text']}" 
                for i, q in enumerate(questions_data)
            ])
            
            question_paper = QuestionPaper(
                title=title,
                subject=subject,
                description=description,
                question_text=combined_question_text,
                answer_text=combined_answer_text,
                total_marks=total_marks
            )
            
            # Save to database
            db.add(question_paper)
            db.commit()
            db.refresh(question_paper)

            # Create individual Question and AnswerScheme records
            created_questions = []
            for i, q_data in enumerate(questions_data):
                try:
                    question = Question(
                        question_paper_id=question_paper.id,
                        question_text=q_data["question_text"].strip(),
                        question_number=q_data.get("question_number", i + 1),
                        max_marks=q_data.get("max_marks", 10),
                        subject_area=subject.lower() if subject else 'general',
                        question_type=q_data.get("question_type", "subjective")
                    )
                    db.add(question)
                    db.commit()
                    db.refresh(question)
                    
                    # Create an AnswerScheme for the question
                    answer_scheme = AnswerScheme(
                        question_id=question.id,
                        model_answer=q_data["answer_text"].strip(),
                        key_points=[],  # Can be populated later
                        marking_criteria={},  # Can be populated later
                        sample_answers=[]  # Can be populated later
                    )
                    db.add(answer_scheme)
                    db.commit()
                    
                    created_questions.append({
                        "question_id": question.id,
                        "question_number": question.question_number,
                        "max_marks": question.max_marks
                    })
                    
                    logger.info(f"Created Question {question.id} and AnswerScheme for QuestionPaper {question_paper.id}")
                    
                except Exception as q_error:
                    logger.error(f"Failed to create Question {i+1}: {str(q_error)}")
                    # Continue with other questions even if one fails
                    continue

            # Convert to dict for JSON response
            created_at = None
            if hasattr(question_paper, 'created_at'):
                dt = question_paper.created_at
                if dt is not None:
                    created_at = dt.isoformat()

            response_data = {
                "id": question_paper.id,
                "message": "Question paper created successfully",
                "title": question_paper.title,
                "subject": question_paper.subject,
                "description": question_paper.description,
                "questions_count": len(created_questions),
                "questions": created_questions,
                "created_at": created_at
            }
            
            return jsonify(response_data), 201

        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": "Failed to create question paper"}), 500
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/question-papers/<int:paper_id>/ocr-verify", methods=["PUT"])
def verify_ocr_text(paper_id):
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        ocr_type = data.get('type')  # 'question' or 'model_answer'
        corrected_text = data.get('corrected_text', '').strip()
        
        if not ocr_type or ocr_type not in ['question', 'model_answer']:
            return jsonify({"error": "Invalid type. Must be 'question' or 'model_answer'"}), 400
        
        if not corrected_text:
            return jsonify({"error": "Missing corrected_text"}), 400
        
        # Get database session
        db = next(get_db())
        try:
            # Find existing question paper
            paper = db.query(QuestionPaper).filter(QuestionPaper.id == paper_id).first()
            if not paper:
                return jsonify({"error": "Question paper not found"}), 404
            
            # Update the appropriate field based on type
            if ocr_type == 'question':
                paper.question_text = corrected_text
                logger.info(f"Updated question text for paper {paper_id}")
            elif ocr_type == 'model_answer':
                paper.answer_text = corrected_text
                logger.info(f"Updated answer text for paper {paper_id}")
            
            # Save changes
            db.commit()
            db.refresh(paper)
            
            return jsonify({"message": "OCR text verified and updated successfully"}), 200

        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": "Database error occurred"}), 500
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/questions/<int:question_id>/submissions", methods=["POST"])
def create_submission(question_id):
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        student_name = request.form.get('student_name')
        if not student_name:
            return jsonify({"error": "Missing student_name"}), 400

        if not student_name or not question_id:
            return jsonify({"error": "Missing student_name or question_id"}), 400

        # Create submissions directory if it doesn't exist
        import os
        submissions_dir = os.path.join('storage', 'submissions')
        os.makedirs(submissions_dir, exist_ok=True)

        # Generate unique filename and save file
        import uuid
        if file.filename:
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(submissions_dir, unique_filename)
            file.save(file_path)
        else:
            return jsonify({"error": "Invalid filename"}), 400

        # Save submission to database
        db = next(get_db())
        try:

            
            # Verify question exists
            question = db.query(Question).filter(Question.id == question_id).first()
            if not question:
                return jsonify({"error": "Question not found"}), 404
            
            submission = Submission(
                question_id=question_id,
                student_name=student_name,
                handwriting_image_path=file_path
            )
            db.add(submission)
            db.commit()
            db.refresh(submission)

            # Get the actual integer ID from the database
            from sqlalchemy import text
            result = db.execute(text("SELECT id FROM submissions WHERE id = :id"), {"id": submission.id}).first()
            actual_submission_id = result[0] if result else None
            
            if not actual_submission_id:
                raise ValueError("Could not retrieve submission ID")

            # Process OCR and evaluation
            try:
                from services.ocr_service import OCRService
                from services.evaluator_service import EvaluatorService
                
                ocr_service = OCRService()
                evaluator_service = EvaluatorService()
                
                # Run OCR synchronously
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Extract text from image
                    logger.info(f"Starting OCR for submission {actual_submission_id}")
                    extracted_text, confidence = loop.run_until_complete(
                        ocr_service.extract_text_from_image(file_path)
                    )
                    
                    # Update submission with OCR results
                    db.execute(
                        text("UPDATE submissions SET extracted_text = :text, ocr_confidence = :conf WHERE id = :id"),
                        {"text": extracted_text, "conf": confidence, "id": actual_submission_id}
                    )
                    db.commit()
                    logger.info(f"OCR completed for submission {actual_submission_id}")
                    
                    # Run automatic evaluation
                    logger.info(f"Starting evaluation for submission {actual_submission_id}")
                    # Type assertion to fix SQLAlchemy Column issue
                    evaluation_result = loop.run_until_complete(
                        evaluator_service.evaluate_submission_with_ocr(db, actual_submission_id)
                    )
                    logger.info(f"Evaluation completed for submission {actual_submission_id}")
                    
                except Exception as ocr_eval_error:
                    logger.error(f"OCR/Evaluation error: {str(ocr_eval_error)}")
                    # Still return submission even if OCR/evaluation fails
                    evaluation_result = None
                finally:
                    loop.close()

            except Exception as process_error:
                logger.error(f"Processing error: {str(process_error)}")
                evaluation_result = None

            # Convert datetime to string for JSON serialization
            submitted_at = None
            if hasattr(submission, 'submitted_at') and submission.submitted_at is not None:
                submitted_at = submission.submitted_at.isoformat()

            response_data = {
                "id": submission.id,
                "question_id": submission.question_id,
                "student_name": submission.student_name,
                "handwriting_image_path": submission.handwriting_image_path,
                "extracted_text": getattr(submission, 'extracted_text', None),
                "ocr_confidence": getattr(submission, 'ocr_confidence', None),
                "submitted_at": submitted_at
            }
            
            # Add evaluation result if available
            if evaluation_result:
                response_data["evaluation"] = evaluation_result

            return jsonify(response_data), 201

        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            # Delete uploaded file if database operation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"error": "Database error occurred"}), 500
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/submissions/<int:submission_id>/evaluation", methods=["GET"])
def get_evaluation_results(submission_id):
    try:
        db = next(get_db())
        try:

            
            # Get evaluation for the submission
            evaluation = db.query(Evaluation).filter(Evaluation.submission_id == submission_id).first()
            if not evaluation:
                return jsonify({"error": "Evaluation not found"}), 404
            
            # Get submission info for context
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                return jsonify({"error": "Submission not found"}), 404
            
            # Convert datetime to string for JSON serialization
            created_at = None
            if hasattr(evaluation, 'created_at') and evaluation.created_at is not None:
                created_at = evaluation.created_at.isoformat()
                
            submitted_at = None
            if hasattr(submission, 'submitted_at') and submission.submitted_at is not None:
                submitted_at = submission.submitted_at.isoformat()

            return jsonify({
                "id": evaluation.id,
                "submission_id": evaluation.submission_id,
                "student_name": submission.student_name,
                "similarity_score": evaluation.similarity_score,
                "marks_awarded": evaluation.marks_awarded,
                "max_marks": evaluation.max_marks,
                "detailed_scores": evaluation.detailed_scores,
                "ai_feedback": evaluation.ai_feedback,
                "evaluation_time": evaluation.evaluation_time,
                "created_at": created_at,
                "submitted_at": submitted_at
            })
            
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": "Database error occurred"}), 500
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/submissions", methods=["GET"])
def get_all_submissions():
    try:
        db = next(get_db())
        try:

            
            # Get all submissions with their evaluations
            submissions = db.query(Submission).all()
            result = []
            
            for submission in submissions:
                # Get evaluation for this submission if it exists
                evaluation = db.query(Evaluation).filter(Evaluation.submission_id == submission.id).first()
                
                submitted_at = None
                if hasattr(submission, 'submitted_at') and submission.submitted_at is not None:
                    submitted_at = submission.submitted_at.isoformat()
                
                submission_data = {
                    "id": submission.id,
                    "question_id": submission.question_id,
                    "student_name": submission.student_name,
                    "handwriting_image_path": submission.handwriting_image_path,
                    "extracted_text": getattr(submission, 'extracted_text', None),
                    "ocr_confidence": getattr(submission, 'ocr_confidence', None),
                    "submitted_at": submitted_at,
                    "evaluation": None
                }
                
                if evaluation:
                    evaluation_created_at = None
                    if hasattr(evaluation, 'created_at') and evaluation.created_at is not None:
                        evaluation_created_at = evaluation.created_at.isoformat()
                        
                    submission_data["evaluation"] = {
                        "id": evaluation.id,
                        "similarity_score": evaluation.similarity_score,
                        "marks_awarded": evaluation.marks_awarded,
                        "max_marks": evaluation.max_marks,
                        "detailed_scores": evaluation.detailed_scores,
                        "ai_feedback": evaluation.ai_feedback,
                        "evaluation_time": evaluation.evaluation_time,
                        "created_at": evaluation_created_at
                    }
                
                result.append(submission_data)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": "Database error occurred"}), 500
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/submissions/<int:submission_id>/retry-ocr", methods=["POST"])
def retry_ocr_processing(submission_id):
    """Retry OCR processing for a specific submission"""
    try:
        db = next(get_db())
        try:
            from sqlalchemy import text
            from services.ocr_service import OCRService
            
            # Get submission
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                return jsonify({"error": "Submission not found"}), 404
            
            handwriting_path = getattr(submission, 'handwriting_image_path', None)
            if not handwriting_path:
                return jsonify({"error": "No handwriting image found for this submission"}), 400
            
            # Run OCR processing
            ocr_service = OCRService()
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                logger.info(f"Starting OCR retry for submission {submission_id}")
                extracted_text, confidence = loop.run_until_complete(
                    ocr_service.extract_text_from_image(handwriting_path)
                )
                
                # Update submission with OCR results
                db.execute(
                    text("UPDATE submissions SET extracted_text = :text, ocr_confidence = :conf WHERE id = :id"),
                    {"text": extracted_text, "conf": confidence, "id": submission_id}
                )
                db.commit()
                logger.info(f"OCR retry completed for submission {submission_id}")
                
                return jsonify({
                    "message": "OCR processing completed successfully",
                    "extracted_text": extracted_text,
                    "ocr_confidence": confidence
                }), 200
                
            except Exception as ocr_error:
                logger.error(f"OCR retry error: {str(ocr_error)}")
                return jsonify({"error": f"OCR processing failed: {str(ocr_error)}"}), 500
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Database error in retry OCR: {str(e)}")
            return jsonify({"error": "Database error occurred"}), 500
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Server error in retry OCR: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/submissions/<int:submission_id>/evaluate", methods=["POST"])
def evaluate_submission(submission_id):
    import asyncio  # Import at the beginning of the function
    try:
        db = next(get_db())
        try:
            from services.evaluator_service import EvaluatorService
            from services.mock_ocr_service import MockOCRService  # Use mock OCR instead
            evaluator = EvaluatorService()
            ocr = MockOCRService()  # Use mock OCR service
            
            # Get submission and question details
            from sqlalchemy import text
            
            # Get submission with explicit column access
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                return jsonify({"error": "Submission not found"}), 404
            
            # Get extracted text value safely
            extracted_text = getattr(submission, 'extracted_text', None)
            handwriting_path = getattr(submission, 'handwriting_image_path', None)
            
            if not extracted_text and handwriting_path:
                # Run OCR synchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    extracted_text, confidence = loop.run_until_complete(
                        ocr.extract_text_from_image(str(handwriting_path))
                    )
                    # Update submission with OCR results
                    db.execute(
                        text("UPDATE submissions SET extracted_text = :text, ocr_confidence = :conf WHERE id = :id"),
                        {"text": extracted_text, "conf": confidence, "id": submission_id}
                    )
                    db.commit()
                finally:
                    loop.close()

            # Run evaluation synchronously
            result = asyncio.new_event_loop().run_until_complete(
                evaluator.evaluate_submission_with_ocr(db, submission_id)
            )
            
            return jsonify({
                "id": submission_id,
                "status": "success",
                "evaluation": result
            })
        except Exception as e:
            logger.error(f"Evaluation error: {str(e)}")
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/debug/submission/<int:submission_id>", methods=["GET"])
def debug_submission(submission_id):
    """Debug endpoint to check submission data in database"""
    try:
        db = next(get_db())
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                return jsonify({"error": "Submission not found"}), 404
            
            return jsonify({
                "id": submission.id,
                "question_id": submission.question_id,
                "student_name": submission.student_name,
                "handwriting_image_path": submission.handwriting_image_path,
                "extracted_text": getattr(submission, 'extracted_text', 'NOT_SET'),
                "extracted_text_type": str(type(getattr(submission, 'extracted_text', None))),
                "extracted_text_length": len(getattr(submission, 'extracted_text', '') or ''),
                "ocr_confidence": getattr(submission, 'ocr_confidence', 'NOT_SET'),
                "submitted_at": submission.submitted_at.isoformat() if hasattr(submission, 'submitted_at') and submission.submitted_at is not None else None,
                "has_extracted_text_attr": hasattr(submission, 'extracted_text'),
                "raw_extracted_text": repr(getattr(submission, 'extracted_text', None))
            })
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/test-ocr", methods=["POST"])
def test_ocr_service():
    """Test endpoint to verify OCR service is working"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Save test file temporarily
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            from services.ocr_service import OCRService
            ocr_service = OCRService()
            
            # Run OCR test
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                logger.info(f"Testing OCR with file: {file.filename}")
                extracted_text, confidence = loop.run_until_complete(
                    ocr_service.extract_text_from_image(temp_path)
                )
                logger.info(f"OCR test result: '{extracted_text}' (confidence: {confidence})")
                
                return jsonify({
                    "success": True,
                    "extracted_text": extracted_text,
                    "confidence": confidence,
                    "text_length": len(extracted_text) if extracted_text else 0,
                    "is_empty": extracted_text == "" if extracted_text is not None else True
                })
            finally:
                loop.close()
                
        except Exception as ocr_error:
            logger.error(f"OCR test failed: {str(ocr_error)}")
            return jsonify({
                "success": False,
                "error": str(ocr_error),
                "error_type": type(ocr_error).__name__
            }), 500
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Test OCR endpoint error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/ocr/process-question-paper", methods=["POST"])
def process_question_paper_ocr():
    """Process uploaded question paper image and extract questions and answers"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        if not file.filename or file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
        if '.' not in file.filename:
            return jsonify({"error": "Invalid file type. Please upload an image file with a valid extension."}), 400
        
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        if file_extension not in allowed_extensions:
            return jsonify({"error": "Invalid file type. Please upload an image file."}), 400
        
        # Save file temporarily
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            from services.ocr_service import OCRService
            ocr_service = OCRService()
            
            # Run OCR
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                logger.info(f"Processing question paper OCR for file: {file.filename}")
                extracted_text, confidence = loop.run_until_complete(
                    ocr_service.extract_text_from_image(temp_path)
                )
                logger.info(f"OCR extraction complete. Text length: {len(extracted_text) if extracted_text else 0}")
                
                if not extracted_text or extracted_text.strip() == "":
                    return jsonify({
                        "error": "No text could be extracted from the image. Please ensure the image is clear and contains readable text."
                    }), 400
                
                # Process the extracted text to separate questions and answers
                question_text, answer_text = classify_question_paper_text(extracted_text)
                
                return jsonify({
                    "success": True,
                    "question_text": question_text,
                    "answer_text": answer_text,
                    "confidence": confidence,
                    "raw_text": extracted_text,
                    "text_length": len(extracted_text)
                })
                
            finally:
                loop.close()
                
        except Exception as ocr_error:
            logger.error(f"Question paper OCR failed: {str(ocr_error)}")
            return jsonify({
                "error": f"OCR processing failed: {str(ocr_error)}",
                "error_type": type(ocr_error).__name__
            }), 500
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Question paper OCR endpoint error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def classify_question_paper_text(text: str) -> tuple[str, str]:
    """
    Classify extracted text into questions and model answers
    Enhanced to better handle multiple questions and answers
    """
    lines = text.strip().split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    if not lines:
        return "", ""
    
    # Keywords that typically indicate question sections
    question_keywords = [
        'question', 'q.', 'q:', 'problem', 'solve', 'find', 'calculate', 
        'determine', 'explain', 'describe', 'what', 'how', 'why', 'which', 
        'where', 'when', 'name', 'list', 'define', 'compare', 'analyze'
    ]
    
    # Keywords that typically indicate answer sections  
    answer_keywords = [
        'answer', 'ans.', 'ans:', 'solution', 'model answer', 'key', 
        'marking scheme', 'rubric', 'response', 'solution:', 'answer:'
    ]
    
    # Look for numbered patterns (1., 2., 3., etc.)
    import re
    numbered_question_pattern = r'^(\d+)[\.\)]\s*'
    numbered_answer_pattern = r'^(\d+)[\.\)]\s*'
    
    # Separate questions and answers
    questions = []
    answers = []
    current_section = None
    current_question_num = None
    current_content = []
    
    for line in lines:
        line_lower = line.lower()
        
        # Check for numbered patterns
        q_match = re.match(numbered_question_pattern, line)
        a_match = re.match(numbered_answer_pattern, line)
        
        # Check if this line indicates a section change
        is_question_line = any(keyword in line_lower for keyword in question_keywords)
        is_answer_line = any(keyword in line_lower for keyword in answer_keywords)
        
        # Detect section headers
        if ('answer' in line_lower and len(line.split()) <= 5) or 'model answer' in line_lower:
            # Save previous content
            if current_section == 'question' and current_content:
                questions.append('\n'.join(current_content))
                current_content = []
            current_section = 'answer'
            current_question_num = None
            continue
        elif ('question' in line_lower and len(line.split()) <= 5) or line_lower.strip() in ['questions', 'q', 'problems']:
            # Save previous content
            if current_section == 'answer' and current_content:
                answers.append('\n'.join(current_content))
                current_content = []
            current_section = 'question'
            current_question_num = None
            continue
        
        # Handle numbered items
        if q_match:
            # Save previous content
            if current_content:
                if current_section == 'question':
                    questions.append('\n'.join(current_content))
                elif current_section == 'answer':
                    answers.append('\n'.join(current_content))
            
            current_question_num = int(q_match.group(1))
            current_section = 'question'
            current_content = [line]
            continue
        elif a_match and current_section != 'question':
            # Save previous content
            if current_content and current_section == 'answer':
                answers.append('\n'.join(current_content))
            
            current_question_num = int(a_match.group(1))
            current_section = 'answer'
            current_content = [line]
            continue
            
        # If we haven't determined a section yet, try to classify based on content
        if current_section is None:
            if is_question_line and not is_answer_line:
                current_section = 'question'
            elif is_answer_line and not is_question_line:
                current_section = 'answer'
            else:
                # Default to question for the first part
                current_section = 'question'
        
        # Add line to current content
        current_content.append(line)
    
    # Save remaining content
    if current_content:
        if current_section == 'question':
            questions.append('\n'.join(current_content))
        elif current_section == 'answer':
            answers.append('\n'.join(current_content))
    
    # If we couldn't classify anything, split roughly in half
    if not questions and not answers:
        mid_point = len(lines) // 2
        questions = ['\n'.join(lines[:mid_point])]
        answers = ['\n'.join(lines[mid_point:])]
    
    # If only one section was found, try to split it
    elif not questions or not answers:
        all_content = questions + answers
        if len(all_content) == 1:
            content_lines = all_content[0].split('\n')
            mid_point = len(content_lines) // 2
            questions = ['\n'.join(content_lines[:mid_point])]
            answers = ['\n'.join(content_lines[mid_point:])]
    
    # Join all questions and answers
    question_text = '\n\n'.join(questions).strip()
    answer_text = '\n\n'.join(answers).strip()
    
    return question_text, answer_text

@app.route("/api/question-papers/<int:question_paper_id>/total-score", methods=["GET"])
def get_question_paper_total_score(question_paper_id):
    """Get total score summary for a question paper"""
    try:
        db = next(get_db())
        try:
            # Get question paper
            question_paper = db.query(QuestionPaper).filter(QuestionPaper.id == question_paper_id).first()
            if not question_paper:
                return jsonify({"error": "Question paper not found"}), 404
            
            # Get all questions for this paper
            questions = db.query(Question).filter(Question.question_paper_id == question_paper_id).all()
            
            # Calculate total possible marks
            total_possible_marks = sum(question.max_marks for question in questions)
            
            # Get all submissions and their evaluations
            question_scores = []
            for question in questions:
                submissions = db.query(Submission).filter(Submission.question_id == question.id).all()
                
                for submission in submissions:
                    if submission.evaluations:
                        evaluation = submission.evaluations[0]  # Get first evaluation
                        question_text = str(question.question_text)
                        question_scores.append({
                            "question_id": question.id,
                            "question_number": question.question_number,
                            "question_text": question_text[:100] + "..." if len(question_text) > 100 else question_text,
                            "student_name": submission.student_name,
                            "marks_awarded": evaluation.marks_awarded,
                            "max_marks": question.max_marks,
                            "submission_id": submission.id
                        })
            
            return jsonify({
                "question_paper_id": question_paper_id,
                "title": question_paper.title,
                "total_possible_marks": total_possible_marks,
                "question_scores": question_scores
            })
            
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error getting total score: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    try:
        # Create database tables
        create_tables()
        logger.info("Database tables created")
        
        # Run Flask app in production mode
        port = 5000  # Changed to match frontend configuration
        logger.info(f"Starting Flask server in production mode on port {port}...")
        app.run(
            host="127.0.0.1",
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise