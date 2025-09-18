from fastapi import FastAPI, Form, Depends
from typing import Optional
import uvicorn
from sqlalchemy.orm import Session
from database import get_db, create_tables
from models import QuestionPaper
import logging

# Configure basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "running"}

@app.post("/api/question-papers")
async def create_question_paper(
    title: str = Form(...),
    subject: str = Form(...),
    description: Optional[str] = Form(None),
    question_text: str = Form(...),
    answer_text: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Creating question paper: {title}")
        question_paper = QuestionPaper(
            title=title,
            subject=subject,
            description=description,
            question_text=question_text,
            answer_text=answer_text
        )
        db.add(question_paper)
        db.commit()
        db.refresh(question_paper)
        return question_paper
    except Exception as e:
        logger.error(f"Error creating question paper: {str(e)}")
        raise

if __name__ == "__main__":
    # Create tables
    create_tables()
    
    # Start server without any fancy configuration
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        log_level="debug"
    )