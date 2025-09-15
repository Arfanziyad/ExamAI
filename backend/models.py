from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class QuestionPaper(Base):
    __tablename__ = "question_papers"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    description = Column(Text)
    file_path = Column(String, nullable=False)
    answer_file_path = Column(String, nullable=False)
    question_text = Column(Text)  # OCR extracted text from question paper
    answer_text = Column(Text)    # OCR extracted text from model answer
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = relationship("Question", back_populates="question_paper", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_paper_id = Column(Integer, ForeignKey("question_papers.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_number = Column(Integer, nullable=False)
    max_marks = Column(Integer, default=10)
    subject_area = Column(String, default="general")
    
    # Relationships
    question_paper = relationship("QuestionPaper", back_populates="questions")
    answer_scheme = relationship("AnswerScheme", back_populates="question", uselist=False, cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="question", cascade="all, delete-orphan")

class AnswerScheme(Base):
    __tablename__ = "answer_schemes"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    model_answer = Column(Text, nullable=False)
    key_points = Column(JSON)  # List of key points
    marking_criteria = Column(JSON)  # Detailed marking criteria
    sample_answers = Column(JSON)  # Sample good/bad answers
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    question = relationship("Question", back_populates="answer_scheme")

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    student_name = Column(String, nullable=False)
    handwriting_image_path = Column(String, nullable=False)
    extracted_text = Column(Text)  # OCR result
    ocr_confidence = Column(Float)  # OCR confidence score
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    question = relationship("Question", back_populates="submissions")
    evaluation = relationship("Evaluation", back_populates="submission", uselist=False, cascade="all, delete-orphan")

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    
    # AI Evaluation Results
    similarity_score = Column(Float, nullable=False)
    marks_awarded = Column(Integer, nullable=False)
    max_marks = Column(Integer, nullable=False)
    detailed_scores = Column(JSON)  # Breakdown of scores
    ai_feedback = Column(Text, nullable=False)
    
    # Manual Override (if teacher modifies)
    manual_marks = Column(Integer)
    manual_feedback = Column(Text)
    is_manually_overridden = Column(Integer, default=0)  # Boolean as integer for SQLite
    
    # Metadata
    evaluation_time = Column(Float)  # Time taken for evaluation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    submission = relationship("Submission", back_populates="evaluation")