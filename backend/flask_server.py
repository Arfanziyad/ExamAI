from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_db, create_tables
from models import QuestionPaper
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
                result.append({
                    "id": paper.id,
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

            # Convert to dict for JSON response
            created_at = None
            if hasattr(question_paper, 'created_at'):
                dt = question_paper.created_at
                if dt is not None:
                    created_at = dt.isoformat()

            response = {
                "id": question_paper.id,
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
            from models import Submission, Question, AnswerScheme
            
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
            from models import Evaluation, Submission
            
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
            from models import Submission, Evaluation
            
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

@app.route("/api/submissions/<int:submission_id>/evaluate", methods=["POST"])
def evaluate_submission(submission_id):
    try:
        db = next(get_db())
        try:
            from services.evaluator_service import EvaluatorService
            from services.ocr_service import OCRService
            evaluator = EvaluatorService()
            ocr = OCRService()
            
            # Get submission and question details
            from models import Submission, Question, QuestionPaper, Evaluation
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
                import asyncio
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