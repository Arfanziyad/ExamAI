from flask import Flask, request, jsonify, g
from flask_cors import CORS
from database import SessionLocal, engine
from models import QuestionPaper, Base
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import traceback
from typing import Dict, Optional, Union
from werkzeug.datastructures import ImmutableMultiDict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Ensure database and tables exist
Base.metadata.create_all(bind=engine)

def get_db():
    """Get the database session for the current request."""
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db

@app.teardown_appcontext
def teardown_db(exception=None):
    """Close the database session at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_request_data() -> Dict[str, str]:
    """Extract and validate request data from either JSON or form data."""
    if request.is_json:
        data = request.get_json()
        if not isinstance(data, dict):
            return {}
    else:
        data = request.form.to_dict()
    return data

def validate_data(data: Dict[str, str]) -> Optional[Dict[str, str]]:
    """Validate the request data and return error message if invalid."""
    required_fields = ['title', 'subject', 'description', 'question_text', 'answer_text']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return {"error": f"Missing required fields: {', '.join(missing_fields)}"}
    return None

@app.route('/api/question-papers', methods=['POST'])
def create_question_paper():
    try:
        # Get and validate data
        data = get_request_data()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        validation_error = validate_data(data)
        if validation_error:
            return jsonify(validation_error), 400
        
        # Create question paper
        question_paper = QuestionPaper(
            title=data['title'],
            subject=data['subject'],
            description=data['description'],
            question_text=data['question_text'],
            answer_text=data['answer_text']
        )
        
        # Save to database
        db = get_db()
        db.add(question_paper)
        db.commit()
        
        return jsonify({
            "message": "Question paper created successfully",
            "id": question_paper.id
        }), 201
        
    except SQLAlchemyError as e:
        db = get_db()
        db.rollback()
        logger.error(f"Database error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error(f"Error creating question paper: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    try:
        db = get_db()
        # Use SQLAlchemy text() for raw SQL
        db.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "database": "disconnected"}), 500

if __name__ == '__main__':
    # Run in production mode (non-debug) with proper host binding
    logger.info("Starting production server on port 5000")
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)