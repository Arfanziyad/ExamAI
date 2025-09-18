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

@app.route("/api/submissions", methods=["POST"])
def create_submission():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        student_name = request.form.get('student_name')
        question_id = request.form.get('question_id')

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
            from models import Submission
            submission = Submission(
                question_id=question_id,
                student_name=student_name,
                handwriting_image_path=file_path
            )
            db.add(submission)
            db.commit()
            db.refresh(submission)

            # Convert datetime to string for JSON serialization
            submitted_at = None
            if hasattr(submission, 'submitted_at') and submission.submitted_at is not None:
                submitted_at = submission.submitted_at.isoformat()

            return jsonify({
                "id": submission.id,
                "student_name": submission.student_name,
                "submitted_at": submitted_at,
                "file_path": submission.handwriting_image_path
            }), 201

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

if __name__ == "__main__":
    try:
        # Create database tables
        create_tables()
        logger.info("Database tables created")
        
        # Run Flask app in production mode
        port = 8000
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