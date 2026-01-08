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

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "ExamAI Backend"})

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
        subject = str(data.get("subject", "General")).strip()
        description = str(data.get("description", "")).strip()
        questions_data = data.get("questions", [])

        # Set default subject if empty
        if not subject:
            subject = "General"

        # Check required fields
        if not title:
            return jsonify({"error": "Title is required"}), 400
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
                        question_type=q_data.get("question_type", "subjective"),
                        # OR Groups Support
                        or_group_id=q_data.get("or_group_id"),
                        # Sub-question support
                        main_question_number=q_data.get("main_question_number"),
                        sub_question=q_data.get("sub_question", ""),
                        is_attempted=0
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

@app.route("/api/question-papers/<int:paper_id>/or-groups/<string:student_name>", methods=["GET"])
def get_or_group_summary(paper_id, student_name):
    """Get OR group evaluation summary for a specific student"""
    try:
        # Get database session
        db = next(get_db())
        try:
            # Use the evaluator service to get OR group summary
            evaluator_service = EvaluatorService()
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            summary = loop.run_until_complete(
                evaluator_service.get_or_group_evaluation_summary(db, paper_id, student_name)
            )
            
            return jsonify({
                "status": "success",
                "data": summary
            }), 200
            
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": "Failed to get OR group summary"}), 500
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

@app.route("/api/question-papers/<int:paper_id>/submissions", methods=["POST"])
def create_multi_question_submission(paper_id):
    """Submit student answer for a multi-question paper with automatic answer mapping"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        student_name = request.form.get('student_name')
        if not student_name:
            return jsonify({"error": "Missing student_name"}), 400

        # Get question paper and its questions
        db = next(get_db())
        try:
            question_paper = db.query(QuestionPaper).filter(QuestionPaper.id == paper_id).first()
            if not question_paper:
                return jsonify({"error": "Question paper not found"}), 404
            
            questions = db.query(Question).filter(Question.question_paper_id == paper_id).all()
            if not questions:
                return jsonify({"error": "No questions found in this paper"}), 404

            # Create submissions directory if it doesn't exist
            import os
            submissions_dir = os.path.join('storage', 'submissions')
            os.makedirs(submissions_dir, exist_ok=True)

            # Generate unique filename and save file
            import uuid
            if file.filename:
                file_extension = os.path.splitext(file.filename)[1]
                unique_filename = f"paper_{paper_id}_{student_name}_{uuid.uuid4()}{file_extension}"
                file_path = os.path.join(submissions_dir, unique_filename)
                file.save(file_path)
            else:
                return jsonify({"error": "Invalid filename"}), 400

            # Process OCR to extract full text
            import asyncio
            from services.ocr_service import OCRService
            
            async def process_ocr():
                ocr_service = OCRService()
                try:
                    return await ocr_service.extract_text_from_image(file_path)
                except Exception as e:
                    logger.warning(f"OCR failed, checking for text fallback: {str(e)}")
                    # Fallback: try to read text file content if it's a text file
                    if file_path.endswith('.txt'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            return f.read(), 0.9
                    raise
                
            extracted_text, ocr_confidence = asyncio.run(process_ocr())
            
            # Use answer sequence service to map answers to questions
            from services.answer_sequence_service import analyze_answer_sequence
            
            expected_questions = [{
                'question_number': q.question_number,
                'question_text': q.question_text,
                'max_marks': q.max_marks,
                'question_id': q.id,
                'or_group_id': q.or_group_id
            } for q in questions]
            
            sequence_analysis = analyze_answer_sequence(extracted_text, expected_questions)
            
            # Track OR groups and which questions were answered
            or_groups_attempted = {}  # {or_group_id: question_id}
            answered_questions = set()  # Set of question_numbers that have answers
            
            # First pass: Identify which questions have actual answers
            for question in questions:
                question_num = str(question.question_number)
                
                # Extract answer for this specific question
                answer_text = ""
                if sequence_analysis and sequence_analysis.get('parsed_answers'):
                    parsed_answers = sequence_analysis['parsed_answers']
                    answer_text = parsed_answers.get(question_num, "")
                    
                    # Try alternative keys if exact match not found
                    if not answer_text:
                        for key, text in parsed_answers.items():
                            if key.startswith(f"{question_num}_") or key.startswith(f"{question_num}."):
                                answer_text = text
                                break
                
                # Check if this question has a meaningful answer (not just the full text fallback)
                if answer_text.strip() and answer_text != extracted_text:
                    answered_questions.add(question_num)
                    
                    # Track OR group attempt
                    if question.or_group_id:
                        if question.or_group_id not in or_groups_attempted:
                            or_groups_attempted[question.or_group_id] = question.id
            
            # Create submissions and evaluate only eligible questions
            submission_results = []
            total_marks = 0
            skipped_questions = []
            
            for question in questions:
                question_num = str(question.question_number)
                
                # Check if this question should be skipped due to OR group logic
                should_skip = False
                skip_reason = ""
                
                if question.or_group_id:
                    # If this OR group has been attempted by another question, skip this one
                    if question.or_group_id in or_groups_attempted:
                        if or_groups_attempted[question.or_group_id] != question.id:
                            should_skip = True
                            skip_reason = f"Skipped - OR group {question.or_group_id} already attempted"
                            skipped_questions.append({
                                "question_number": question.question_number,
                                "question_text": question.question_text[:100] + "...",
                                "reason": skip_reason,
                                "or_group_id": question.or_group_id
                            })
                
                if should_skip:
                    continue
                
                # Extract answer for this specific question
                answer_text = ""
                if sequence_analysis and sequence_analysis.get('parsed_answers'):
                    parsed_answers = sequence_analysis['parsed_answers']
                    answer_text = parsed_answers.get(question_num, "")
                    
                    # Try alternative keys if exact match not found
                    if not answer_text:
                        for key, text in parsed_answers.items():
                            if key.startswith(f"{question_num}_") or key.startswith(f"{question_num}."):
                                answer_text = text
                                break
                
                # If no specific answer found, skip this question (don't use full text fallback)
                if not answer_text.strip() or answer_text == extracted_text:
                    skipped_questions.append({
                        "question_number": question.question_number,
                        "question_text": question.question_text[:100] + "...",
                        "reason": "No answer detected for this question",
                        "or_group_id": question.or_group_id
                    })
                    continue
                
                # Create submission for this question
                submission = Submission(
                    question_id=question.id,
                    student_name=student_name,
                    handwriting_image_path=file_path,
                    extracted_text=answer_text,
                    ocr_confidence=ocr_confidence
                )
                
                db.add(submission)
                db.commit()
                db.refresh(submission)
                
                # Evaluate submission immediately
                from services.evaluator_service import EvaluatorService
                evaluator_service = EvaluatorService()
                
                try:
                    evaluation_result = asyncio.run(evaluator_service.evaluate_submission(
                        db, submission.id
                    ))
                    
                    if evaluation_result:
                        total_marks += evaluation_result.get('marks_awarded', 0)
                        
                        submission_results.append({
                            "submission_id": submission.id,
                            "question_number": question.question_number,
                            "question_text": question.question_text[:100] + "...",
                            "extracted_answer": answer_text[:200] + "...",
                            "marks_awarded": evaluation_result.get('marks_awarded', 0),
                            "max_marks": question.max_marks,
                            "or_group_id": question.or_group_id,
                            "evaluation": {
                                "similarity_score": evaluation_result.get('similarity_score', 0),
                                "ai_feedback": evaluation_result.get('ai_feedback', 'No feedback available')
                            }
                        })
                    else:
                        submission_results.append({
                            "submission_id": submission.id,
                            "question_number": question.question_number,
                            "question_text": question.question_text[:100] + "...",
                            "extracted_answer": answer_text[:200] + "...",
                            "marks_awarded": 0,
                            "max_marks": question.max_marks,
                            "evaluation": None
                        })
                        
                except Exception as eval_error:
                    logger.error(f"Evaluation failed for question {question.id}: {str(eval_error)}")
                    submission_results.append({
                        "submission_id": submission.id,
                        "question_number": question.question_number,
                        "question_text": question.question_text[:100] + "...",
                        "extracted_answer": answer_text[:200] + "...",
                        "marks_awarded": 0,
                        "max_marks": question.max_marks,
                        "or_group_id": question.or_group_id,
                        "evaluation": None,
                        "error": str(eval_error)
                    })
            
            # Calculate total possible marks considering OR groups
            # For OR groups: only count the max marks of ONE question from each group
            or_group_max_marks = {}
            total_possible_marks = 0
            
            for q in questions:
                if q.or_group_id:
                    # Track max marks per OR group (only count once per group)
                    if q.or_group_id not in or_group_max_marks:
                        or_group_max_marks[q.or_group_id] = q.max_marks
                    else:
                        # Take the maximum marks among questions in the same OR group
                        or_group_max_marks[q.or_group_id] = max(or_group_max_marks[q.or_group_id], q.max_marks)
                else:
                    # Not in OR group, count normally
                    total_possible_marks += q.max_marks
            
            # Add OR group marks (one per group)
            total_possible_marks += sum(or_group_max_marks.values())
            
            return jsonify({
                "success": True,
                "message": "Multi-question submission processed successfully",
                "student_name": student_name,
                "question_paper_title": question_paper.title,
                "total_marks_awarded": total_marks,
                "total_possible_marks": total_possible_marks,
                "percentage": round((total_marks / total_possible_marks) * 100, 2) if total_possible_marks > 0 else 0,
                "submissions": submission_results,
                "skipped_questions": skipped_questions,
                "or_groups_info": {
                    "attempted_groups": or_groups_attempted,
                    "total_or_groups": len(or_group_max_marks)
                },
                "sequence_analysis": {
                    "detected_sequence": sequence_analysis.get('answer_sequence', []) if sequence_analysis else [],
                    "confidence": sequence_analysis.get('sequence_confidence', 0) if sequence_analysis else 0
                },
                "ocr_info": {
                    "confidence": ocr_confidence,
                    "extracted_text_preview": extracted_text[:300] + "..."
                }
            }), 201
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Multi-question submission error: {str(e)}")
        return jsonify({"error": f"Failed to process submission: {str(e)}"}), 500

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

            
            # Get all submissions with their evaluations and question paper info
            submissions = db.query(Submission).join(Question).all()
            result = []
            
            for submission in submissions:
                # Get evaluation for this submission if it exists
                evaluation = db.query(Evaluation).filter(Evaluation.submission_id == submission.id).first()
                
                # Get question to retrieve question_paper_id
                question = db.query(Question).filter(Question.id == submission.question_id).first()
                question_paper_id = question.question_paper_id if question else None
                
                submitted_at = None
                if hasattr(submission, 'submitted_at') and submission.submitted_at is not None:
                    submitted_at = submission.submitted_at.isoformat()
                
                submission_data = {
                    "id": submission.id,
                    "question_id": submission.question_id,
                    "question_paper_id": question_paper_id,
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

@app.route("/api/submissions/<int:submission_id>/evaluate-with-sequence", methods=["POST"])
def evaluate_submission_with_sequence(submission_id):
    """Evaluate submission with flexible answer sequence analysis"""
    try:
        # Get database session
        db = next(get_db())
        try:
            # Check if submission exists
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                return jsonify({"error": "Submission not found"}), 404
                
            # Get optional parameters
            data = request.get_json() if request.is_json else {}
            force_reanalysis = data.get('force_reanalysis', False)
            
            # Run evaluation with sequence analysis
            evaluator_service = EvaluatorService()
            
            # Use asyncio to run the async method
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    evaluator_service.evaluate_submission_with_sequence_analysis(
                        db, submission_id, force_reanalysis
                    )
                )
            finally:
                loop.close()
            
            return jsonify({
                "id": submission_id,
                "status": "success", 
                "evaluation": result,
                "sequence_analysis": result.get('sequence_analysis', {}),
                "message": "Evaluation completed with answer sequence analysis"
            })
            
        except Exception as e:
            logger.error(f"Sequence evaluation error: {str(e)}")
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
                
                # NEW: Automatically parse and create questions if title/subject provided
                title = request.form.get('title', '').strip()
                subject = request.form.get('subject', '').strip()
                description = request.form.get('description', '').strip()
                
                if title and subject:
                    # Parse the extracted text into individual questions
                    parsed_questions = parse_multiple_questions_from_ocr(extracted_text)
                    
                    if parsed_questions:
                        logger.info(f"Parsed {len(parsed_questions)} questions from OCR text")
                        
                        # Create question paper with individual questions
                        db = next(get_db())
                        try:
                            # Calculate total marks
                            total_marks = sum(q.get('max_marks', 5) for q in parsed_questions)
                            
                            # Create question paper
                            question_paper = QuestionPaper(
                                title=title,
                                subject=subject,
                                description=description,
                                question_text=question_text,
                                answer_text=answer_text,
                                total_marks=total_marks
                            )
                            
                            db.add(question_paper)
                            db.commit()
                            db.refresh(question_paper)
                            
                            # Create individual questions
                            created_questions = []
                            for i, q_data in enumerate(parsed_questions):
                                question = Question(
                                    question_paper_id=question_paper.id,
                                    question_text=q_data.get('question_text', ''),
                                    question_number=i + 1,
                                    max_marks=q_data.get('max_marks', 5),
                                    subject_area=subject.lower(),
                                    question_type=q_data.get('question_type', 'subjective'),
                                    main_question_number=q_data.get('main_question_number'),
                                    sub_question=q_data.get('sub_question'),
                                    or_group_id=q_data.get('or_group_id'),
                                    is_attempted=0
                                )
                                db.add(question)
                                db.commit()
                                db.refresh(question)
                                
                                # Create answer scheme
                                if q_data.get('answer_text'):
                                    answer_scheme = AnswerScheme(
                                        question_id=question.id,
                                        model_answer=q_data['answer_text'],
                                        key_points=[],
                                        marking_criteria={},
                                        sample_answers=[]
                                    )
                                    db.add(answer_scheme)
                                    db.commit()
                                
                                created_questions.append({
                                    "question_id": question.id,
                                    "question_number": question.question_number,
                                    "max_marks": question.max_marks
                                })
                            
                            logger.info(f"Successfully created question paper {question_paper.id} with {len(created_questions)} questions")
                            
                            return jsonify({
                                "success": True,
                                "question_paper_created": True,
                                "id": question_paper.id,
                                "title": question_paper.title,
                                "questions_created": len(created_questions),
                                "question_text": question_text,
                                "answer_text": answer_text,
                                "confidence": confidence,
                                "raw_text": extracted_text,
                                "text_length": len(extracted_text)
                            })
                            
                        except Exception as db_error:
                            logger.error(f"Failed to create questions from OCR: {str(db_error)}")
                            db.rollback()
                            # Fall back to just returning OCR text
                        finally:
                            db.close()
                
                # Default: Just return OCR text (backward compatibility)
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
    Enhanced to better handle multiple questions and answers including Q1, Ans1 patterns
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
    
    # Enhanced patterns to recognize Q1, Q2, Ans1, Ans2, etc.
    import re
    # Original numbered patterns (1., 2., 3., etc.)
    numbered_question_pattern = r'^(\d+)[\.\)]\s*'
    numbered_answer_pattern = r'^(\d+)[\.\)]\s*'
    
    # New patterns for Q1, Q2, Ans1, Ans2, etc.
    q_numbered_pattern = r'^[Qq](\d+)[\.\:\s]*'  # Matches Q1, q1, Q1:, Q1., etc.
    ans_numbered_pattern = r'^[Aa]ns(\d+)[\.\:\s]*'  # Matches Ans1, ans1, Ans1:, etc.
    
    # Separate questions and answers
    questions = []
    answers = []
    current_section = None
    current_question_num = None
    current_content = []
    
    for line in lines:
        line_lower = line.lower()
        
        # Check for all patterns
        q_match = re.match(numbered_question_pattern, line)
        a_match = re.match(numbered_answer_pattern, line)
        q_num_match = re.match(q_numbered_pattern, line)
        ans_num_match = re.match(ans_numbered_pattern, line)
        
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
        
        # Handle Q1, Q2, etc. patterns
        if q_num_match:
            # Save previous content
            if current_content:
                if current_section == 'question':
                    questions.append('\n'.join(current_content))
                elif current_section == 'answer':
                    answers.append('\n'.join(current_content))
            
            current_question_num = int(q_num_match.group(1))
            current_section = 'question'
            current_content = [line]
            continue
            
        # Handle Ans1, Ans2, etc. patterns
        if ans_num_match:
            # Save previous content
            if current_content:
                if current_section == 'question':
                    questions.append('\n'.join(current_content))
                elif current_section == 'answer':
                    answers.append('\n'.join(current_content))
            
            current_question_num = int(ans_num_match.group(1))
            current_section = 'answer'
            current_content = [line]
            continue
        
        # Handle numbered items (original logic)
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

def detect_or_groups_in_text(text: str) -> dict[int, str]:
    """
    Detect OR groups in text by looking for "OR" patterns
    Returns a mapping of main_question_number -> group_id
    Groups entire questions (with all sub-parts) rather than individual sub-questions
    More precise OR detection - only groups immediately adjacent questions
    """
    lines = text.strip().split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    or_groups = {}
    group_counter = 1
    
    import re
    
    # Find all OR positions and the questions around them
    or_positions = []
    for i, line in enumerate(lines):
        or_pattern = r'^\s*OR\s*$|^\s*or\s*$|^\s*Or\s*$'
        if re.match(or_pattern, line):
            or_positions.append(i)
    
    # For each OR, find the immediately adjacent questions (more precise)
    for or_pos in or_positions:
        questions_before = set()
        questions_after = set()
        
        # Look backwards for questions before OR (but stop at first non-question/answer content)
        for j in range(or_pos - 1, -1, -1):
            prev_line = lines[j].strip()
            
            # Skip answer lines
            if re.match(r'^[Aa][Nn][Ss]', prev_line):
                continue
                
            # Check if it's a question line
            q_patterns = [
                r'^[Qq]uestion\s+(\d+)[\s\.\:]*',
                r'^[Qq](\d+)[\s\.\:]*',
                r'^[Qq](\d+)([a-z])[\s\.\:]*',  # Q1a, Q2b format
                r'^(\d+)[\s\.\)]*[a-z]?[\s\.\)]*',  # 1a, 2b format
            ]
            
            question_found = False
            for pattern in q_patterns:
                match = re.match(pattern, prev_line)
                if match:
                    main_question_num = int(match.group(1))
                    questions_before.add(main_question_num)
                    question_found = True
                    break
            
            # If we found a question, check if the next line back is related (same question family)
            if question_found and j > 0:
                # Continue only if the previous questions are part of the same main question number
                prev_main_nums = list(questions_before)
                if prev_main_nums:
                    current_main = prev_main_nums[0]
                    # Look for more sub-questions of the same main question
                    continue_search = False
                    for k in range(j - 1, max(-1, j - 5), -1):  # Look back max 5 lines
                        earlier_line = lines[k].strip()
                        if re.match(r'^[Aa][Nn][Ss]', earlier_line):
                            continue
                        for pattern in q_patterns:
                            match = re.match(pattern, earlier_line)
                            if match and int(match.group(1)) == current_main:
                                questions_before.add(current_main)
                                continue_search = True
                                break
                        if not continue_search:
                            break
            break  # Stop after finding the first question group before OR
        
        # Look forwards for questions after OR (but limit scope)
        for j in range(or_pos + 1, min(len(lines), or_pos + 10)):  # Limit to 10 lines after OR
            next_line = lines[j].strip()
            
            # Skip answer lines
            if re.match(r'^[Aa][Nn][Ss]', next_line):
                continue
                
            # Check if it's a question line
            q_patterns = [
                r'^[Qq]uestion\s+(\d+)[\s\.\:]*',
                r'^[Qq](\d+)[\s\.\:]*',
                r'^[Qq](\d+)([a-z])[\s\.\:]*',  # Q1a, Q2b format
                r'^(\d+)[\s\.\)]*[a-z]?[\s\.\)]*',  # 1a, 2b format
            ]
            
            for pattern in q_patterns:
                match = re.match(pattern, next_line)
                if match:
                    main_question_num = int(match.group(1))
                    questions_after.add(main_question_num)
                    # Only take the first question after OR (don't be greedy)
                    break
            
            # Stop after finding the first question after OR
            if questions_after:
                break
            
            # Stop if we hit another OR
            if re.match(r'^\s*OR\s*$|^\s*or\s*$|^\s*Or\s*$', next_line):
                break
        
        # Assign OR groups to questions found before and after this OR
        if questions_before and questions_after:
            group_id = f"or_group_{group_counter}"
            for q_num in questions_before:
                or_groups[q_num] = group_id
            for q_num in questions_after:
                or_groups[q_num] = group_id
            group_counter += 1
    
    return or_groups

def parse_multiple_questions_from_ocr(text: str) -> list[dict]:
    """
    Parse OCR text to extract multiple questions and their corresponding answers
    Handles sub-questions (1a, 1b, 1c, 2a, 2b, etc.) and groups them properly
    Now includes automatic OR group detection for entire questions
    Returns a list of dictionaries with question_text, answer_text, and question_number
    """
    lines = text.strip().split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    if not lines:
        return []
    
    # First, detect OR groups in the text (for main questions)
    or_group_mappings = detect_or_groups_in_text(text)
    
    import re
    # Enhanced patterns for sub-questions and answers
    question_basic_pattern = r'^[Qq]uestion\s+(\d+)[\s\:\.\-]*(.*)$'  # Question 1:, Question 2:, etc.
    question_basic_subq_pattern = r'^[Qq]uestion\s+(\d+)([a-z])[\s\:\.\-]*(.*)$'  # Question 1a:, Question 1b:, etc.
    q_numbered_pattern = r'^[Qq](\d+)[\s\.\:]*(.*)$'  # Q1, Q2, etc.
    q_subquestion_pattern = r'^[Qq](\d+)([a-z])[\s\.\)\:]*(.*)$'  # Q1a, Q1b, Q2a, Q2b, etc.
    numbered_question_pattern = r'^(\d+)[\.\)]\s*(.*)$'  # 1., 2., etc.
    simple_subquestion_pattern = r'^(\d+)([a-z])[\s\.\)\:]*(.*)$'  # 1a, 1b, 2a, 2b, etc.
    
    # Answer patterns - more flexible to handle various formats
    answer_basic_pattern = r'^[Aa]nswer\s+(\d+)[\s\:\.\-]*(.*)$'  # Answer 1:, Answer 2:, etc.
    answer_basic_subq_pattern = r'^[Aa]nswer\s+(\d+)([a-z])[\s\:\.\-]*(.*)$'  # Answer 1a:, Answer 1b:, etc.
    ans_numbered_pattern = r'^[Aa][Nn][Ss]\s*(\d+)[\s\.\:]*(.*)$'  # ANS1, ANS 1, ans1, etc.
    ans_subquestion_pattern = r'^[Aa][Nn][Ss]\s*(\d+)\s*([a-z])[\s\.\:]*(.*)$'  # ANS1a, ANS 1a, ANS1 a, etc.
    simple_ans_subquestion_pattern = r'^[Aa][Nn][Ss](\d+)([a-z])[\s\.\:]*(.*)$'  # ANS1a (no space)

    questions_dict = {}  # {question_key: {'question': text, 'answer': text, 'main_num': int, 'sub': str}}
    
    # First pass: collect all questions and answers separately
    for line in lines:
        # Skip OR lines
        if re.match(r'^\s*OR\s*$|^\s*or\s*$|^\s*Or\s*$', line):
            continue
        
        # Check for Q-style sub-questions like "Q1a. What is..." or "Q2b) Calculate..."
        q_subq_match = re.match(q_subquestion_pattern, line)
        if q_subq_match:
            main_num = int(q_subq_match.group(1))
            sub_letter = q_subq_match.group(2)
            question_text = q_subq_match.group(3).strip()
            question_key = f"{main_num}{sub_letter}"
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': main_num, 'sub': sub_letter
                }
            questions_dict[question_key]['question'] = question_text
            continue
        
        # Check for simple sub-questions like "1a. What is..." or "2b) Calculate..."
        subq_match = re.match(simple_subquestion_pattern, line)
        if subq_match:
            main_num = int(subq_match.group(1))
            sub_letter = subq_match.group(2)
            question_text = subq_match.group(3).strip()
            question_key = f"{main_num}{sub_letter}"
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': main_num, 'sub': sub_letter
                }
            questions_dict[question_key]['question'] = question_text
            continue
            
        # Check for basic sub-questions like "Question 1a:" first  
        q_basic_subq_match = re.match(question_basic_subq_pattern, line)
        if q_basic_subq_match:
            main_num = int(q_basic_subq_match.group(1))
            sub_letter = q_basic_subq_match.group(2)
            question_text = q_basic_subq_match.group(3).strip()
            question_key = f"{main_num}{sub_letter}"
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': main_num, 'sub': sub_letter
                }
            questions_dict[question_key]['question'] = question_text
            continue
            
        # Check for basic questions like "Question 1:" first
        q_basic_match = re.match(question_basic_pattern, line)
        if q_basic_match:
            question_num = int(q_basic_match.group(1))
            question_text = q_basic_match.group(2).strip()
            question_key = str(question_num)
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': question_num, 'sub': ''
                }
            questions_dict[question_key]['question'] = question_text
            continue
            
        # Check for main questions like "Q1" or "1."
        q_num_match = re.match(q_numbered_pattern, line)
        if q_num_match:
            question_num = int(q_num_match.group(1))
            question_text = q_num_match.group(2).strip()
            question_key = str(question_num)
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': question_num, 'sub': ''
                }
            questions_dict[question_key]['question'] = question_text
            continue
            
        # Check for numbered patterns like "1. Define..."
        elif re.match(numbered_question_pattern, line):
            num_match = re.match(numbered_question_pattern, line)
            question_num = int(num_match.group(1))
            question_text = num_match.group(2).strip()
            question_key = str(question_num)
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': question_num, 'sub': ''
                }
            questions_dict[question_key]['question'] = question_text
            continue
        
        # Check for sub-question answers like "ANS1a", "ANS 1a", "ANS 1 a", etc.
        ans_subq_match = re.match(ans_subquestion_pattern, line)
        if ans_subq_match:
            main_num = int(ans_subq_match.group(1))
            sub_letter = ans_subq_match.group(2)
            answer_text = ans_subq_match.group(3).strip()
            question_key = f"{main_num}{sub_letter}"
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': main_num, 'sub': sub_letter
                }
            questions_dict[question_key]['answer'] = answer_text
            continue
        
        # Check for simple answer format like "ANS1a" (no space)
        simple_ans_match = re.match(simple_ans_subquestion_pattern, line)
        if simple_ans_match:
            main_num = int(simple_ans_match.group(1))
            sub_letter = simple_ans_match.group(2)
            answer_text = simple_ans_match.group(3).strip()
            question_key = f"{main_num}{sub_letter}"
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': main_num, 'sub': sub_letter
                }
            questions_dict[question_key]['answer'] = answer_text
            continue
        
        # Check for basic sub-question answers like "Answer 1a:" first  
        ans_basic_subq_match = re.match(answer_basic_subq_pattern, line)
        if ans_basic_subq_match:
            main_num = int(ans_basic_subq_match.group(1))
            sub_letter = ans_basic_subq_match.group(2)
            answer_text = ans_basic_subq_match.group(3).strip()
            question_key = f"{main_num}{sub_letter}"
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': main_num, 'sub': sub_letter
                }
            questions_dict[question_key]['answer'] = answer_text
            continue
        
        # Check for basic answers like "Answer 1:" first  
        ans_basic_match = re.match(answer_basic_pattern, line)
        if ans_basic_match:
            answer_num = int(ans_basic_match.group(1))
            answer_text = ans_basic_match.group(2).strip()
            question_key = str(answer_num)
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': answer_num, 'sub': ''
                }
            questions_dict[question_key]['answer'] = answer_text
            continue
        
        # Check for main question answers like "ANS1", "ANS 2", etc.
        ans_num_match = re.match(ans_numbered_pattern, line)
        if ans_num_match:
            answer_num = int(ans_num_match.group(1))
            answer_text = ans_num_match.group(2).strip()
            question_key = str(answer_num)
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': answer_num, 'sub': ''
                }
            questions_dict[question_key]['answer'] = answer_text
            continue
        
        # Additional fallback patterns for answers that might be formatted differently
        # Handle "Answer 1a:", "ANSWER 1b", etc.
        alt_ans_pattern = r'^[Aa]nswer\s*(\d+)\s*([a-z])?\s*[\:\.]?\s*(.*)$'
        alt_ans_match = re.match(alt_ans_pattern, line)
        if alt_ans_match:
            main_num = int(alt_ans_match.group(1))
            sub_letter = alt_ans_match.group(2) or ''
            answer_text = alt_ans_match.group(3).strip()
            question_key = f"{main_num}{sub_letter}" if sub_letter else str(main_num)
            
            if question_key not in questions_dict:
                questions_dict[question_key] = {
                    'question': '', 'answer': '', 
                    'main_num': main_num, 'sub': sub_letter
                }
            questions_dict[question_key]['answer'] = answer_text
            continue

    # Convert to list format and add OR group information
    result = []
    question_counter = 1
    
    # Sort by main question number, then by sub-question letter
    sorted_keys = sorted(questions_dict.keys(), key=lambda x: (
        questions_dict[x]['main_num'],
        questions_dict[x]['sub']
    ))
    
    for question_key in sorted_keys:
        q_data = questions_dict[question_key]
        if q_data['question'].strip():  # Only include if there's actually a question
            main_num = q_data['main_num']
            sub = q_data['sub']
            
            # Create display number (1a, 1b, 2a, etc. or just 1, 2, etc.)
            display_number = f"{main_num}{sub}" if sub else str(main_num)
            
            question_item = {
                'question_number': question_counter,  # Sequential numbering for system
                'display_number': display_number,  # What user sees (1a, 1b, etc.)
                'main_question_number': main_num,  # For OR grouping
                'sub_question': sub,  # Sub-question letter (a, b, c, etc.)
                'question_text': q_data['question'].strip(),
                'answer_text': q_data['answer'].strip(),
                'max_marks': 5 if sub else 10,  # Sub-questions get fewer marks
                'question_type': 'subjective'
            }
            
            # Add OR group information if main question is in an OR group
            if main_num in or_group_mappings:
                question_item['or_group_id'] = or_group_mappings[main_num]
                question_item['or_group_title'] = f"Choose one from OR Group {or_group_mappings[main_num]}"
            
            result.append(question_item)
            question_counter += 1
    
    return result


@app.route("/api/ocr/process-question-paper-structured", methods=["POST"])
def process_question_paper_ocr_structured():
    """
    Process question paper image via OCR and return structured questions for user review
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get optional metadata
        title = request.form.get('title', 'Untitled Question Paper')
        subject = request.form.get('subject', 'General')
        description = request.form.get('description', '')
        
        # Save uploaded file temporarily
        import tempfile
        import os
        import asyncio
        from services.ocr_service import OCRService
        
        temp_path = None
        try:
            # Create temporary file
            filename = file.filename or 'upload'
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_path = temp_file.name
                file.save(temp_path)
            
            logger.info(f"Processing structured question paper OCR for file: {filename}")
            
            # Process OCR (handle async call)
            async def process_ocr():
                ocr_service = OCRService()
                return await ocr_service.extract_text_from_image(temp_path)
            
            extracted_text, confidence = asyncio.run(process_ocr())
            
            logger.info(f"OCR extraction completed. Confidence: {confidence}")
            logger.info(f"Extracted text preview: {extracted_text[:200]}...")
            
            # Parse multiple questions from OCR text
            parsed_questions = parse_multiple_questions_from_ocr(extracted_text)
            
            # Debug logging
            logger.info(f"Parsed {len(parsed_questions)} questions from OCR text")
            for i, q in enumerate(parsed_questions):
                logger.info(f"Question {i+1}: {q.get('display_number', q.get('question_number'))} - {q.get('question_text', 'No text')[:50]}...")
                if q.get('or_group_id'):
                    logger.info(f"  OR Group: {q['or_group_id']}")
            
            logger.info(f"Parsed {len(parsed_questions)} questions from OCR text")
            
            # Create OR group summary for review
            or_groups_summary = {}
            standalone_questions = []
            
            for question in parsed_questions:
                if question.get('or_group_id'):
                    group_id = question['or_group_id']
                    if group_id not in or_groups_summary:
                        or_groups_summary[group_id] = {
                            'group_id': group_id,
                            'title': question.get('or_group_title', f'OR Group {group_id}'),
                            'questions': [],
                            'total_marks': 0
                        }
                    or_groups_summary[group_id]['questions'].append(question)
                    or_groups_summary[group_id]['total_marks'] += question.get('max_marks', 10)
                else:
                    standalone_questions.append(question)
            
            # Return structured data for user review
            return jsonify({
                "success": True,
                "extracted_text": extracted_text,
                "confidence": confidence,
                "questions": parsed_questions,
                "or_groups_summary": {
                    "or_groups": list(or_groups_summary.values()),
                    "standalone_questions": standalone_questions,
                    "total_or_groups": len(or_groups_summary),
                    "auto_detected": len(or_groups_summary) > 0
                },
                "metadata": {
                    "title": title,
                    "subject": subject,
                    "description": description,
                    "filename": filename
                }
            })
            
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Structured question paper OCR endpoint error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
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
            total_possible_marks = 0
            for question in questions:
                total_possible_marks += getattr(question, 'max_marks', 0)
            
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

@app.route("/api/question-papers/<int:question_paper_id>/student-scores", methods=["GET"])
def get_student_aggregated_scores(question_paper_id):
    """Get aggregated scores for all students who attempted this question paper"""
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
            total_possible_marks = 0
            for question in questions:
                total_possible_marks += getattr(question, 'max_marks', 0)
            
            # Get all unique students who submitted answers
            student_scores = {}
            question_details = []
            
            for question in questions:
                question_details.append({
                    "question_id": question.id,
                    "question_number": question.question_number,
                    "question_type": question.question_type,
                    "max_marks": question.max_marks,
                    "question_text": str(question.question_text)[:100] + "..." if len(str(question.question_text)) > 100 else str(question.question_text)
                })
                
                submissions = db.query(Submission).filter(Submission.question_id == question.id).all()
                
                for submission in submissions:
                    student_name = submission.student_name
                    if student_name not in student_scores:
                        student_scores[student_name] = {
                            "student_name": student_name,
                            "total_marks": 0,
                            "questions_attempted": 0,
                            "questions_scored": [],
                            "question_types": {}
                        }
                    
                    if submission.evaluations:
                        evaluation = submission.evaluations[0]  # Get first evaluation
                        marks_awarded = evaluation.marks_awarded
                        student_scores[student_name]["total_marks"] += marks_awarded
                        student_scores[student_name]["questions_attempted"] += 1
                        student_scores[student_name]["questions_scored"].append({
                            "question_id": question.id,
                            "question_number": question.question_number,
                            "question_type": question.question_type,
                            "marks_awarded": marks_awarded,
                            "max_marks": question.max_marks,
                            "submission_id": submission.id
                        })
                        
                        # Track performance by question type
                        q_type = question.question_type
                        if q_type not in student_scores[student_name]["question_types"]:
                            student_scores[student_name]["question_types"][q_type] = {
                                "total_marks": 0,
                                "max_marks": 0,
                                "count": 0
                            }
                        student_scores[student_name]["question_types"][q_type]["total_marks"] += marks_awarded
                        student_scores[student_name]["question_types"][q_type]["max_marks"] += question.max_marks
                        student_scores[student_name]["question_types"][q_type]["count"] += 1
            
            # Calculate percentages and rankings
            student_list = list(student_scores.values())
            student_list.sort(key=lambda x: x["total_marks"], reverse=True)
            
            for i, student in enumerate(student_list):
                student["rank"] = i + 1
                student["percentage"] = (student["total_marks"] / total_possible_marks * 100) if total_possible_marks > 0 else 0
                
                # Calculate type-wise percentages
                for q_type, type_data in student["question_types"].items():
                    if type_data["max_marks"] > 0:
                        type_data["percentage"] = (type_data["total_marks"] / type_data["max_marks"]) * 100
                    else:
                        type_data["percentage"] = 0
            
            return jsonify({
                "question_paper_id": question_paper_id,
                "title": question_paper.title,
                "total_possible_marks": total_possible_marks,
                "total_questions": len(questions),
                "question_details": question_details,
                "student_scores": student_list,
                "students_count": len(student_list)
            })
            
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error getting student aggregated scores: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/question-papers/create-from-ocr", methods=["POST"])
def create_question_paper_from_ocr():
    """
    Create a question paper from OCR-parsed questions with user-selected types
    """
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Get and validate basic fields
        title = str(data.get("title", "")).strip()
        subject = str(data.get("subject", "General")).strip()
        description = str(data.get("description", "")).strip()
        questions_data = data.get("questions", [])

        # Set default subject if empty
        if not subject:
            subject = "General"

        # Check required fields
        if not title:
            return jsonify({"error": "Title is required"}), 400
        if not questions_data or len(questions_data) == 0:
            return jsonify({"error": "At least one question is required"}), 400

        # Validate questions
        for i, q_data in enumerate(questions_data):
            if not q_data.get("question_text", "").strip():
                return jsonify({"error": f"Question text is required for question {i+1}"}), 400
            if not q_data.get("answer_text", "").strip():
                return jsonify({"error": f"Answer text is required for question {i+1}"}), 400
            
            # Validate question type
            question_type = q_data.get("question_type", "subjective")
            if question_type not in ["subjective", "coding"]:
                return jsonify({"error": f"Invalid question type for question {i+1}. Must be 'subjective' or 'coding'"}), 400

        # Get database session
        db = next(get_db())
        try:
            # Calculate total marks for the question paper
            total_marks = sum(q_data.get("max_marks", 10) for q_data in questions_data)
            
            # Create question paper
            # For backward compatibility, combine all questions into question_text and answer_text
            combined_question_text = "\n\n".join([
                f"Question {q.get('question_number', i+1)}: {q['question_text']}" 
                for i, q in enumerate(questions_data)
            ])
            combined_answer_text = "\n\n".join([
                f"Answer {q.get('question_number', i+1)}: {q['answer_text']}" 
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

            # Create individual Question and AnswerScheme records with question types
            created_questions = []
            for i, q_data in enumerate(questions_data):
                try:
                    question = Question(
                        question_paper_id=question_paper.id,
                        question_text=q_data["question_text"].strip(),
                        question_number=q_data.get("question_number", i + 1),
                        max_marks=q_data.get("max_marks", 10),
                        subject_area=question_paper.subject.lower() if question_paper.subject else 'general',
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
                        "max_marks": question.max_marks,
                        "question_type": question.question_type
                    })
                    
                except Exception as e:
                    logger.error(f"Error creating question {i+1}: {str(e)}")
                    continue
            
            return jsonify({
                "success": True,
                "message": "Question paper created successfully from OCR",
                "id": question_paper.id,
                "title": question_paper.title,
                "total_marks": total_marks,
                "questions_created": len(created_questions),
                "questions": created_questions
            })
            
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Create question paper from OCR error: {str(e)}")
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