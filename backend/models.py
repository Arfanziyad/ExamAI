from database import Base, create_tables, engine
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class QuestionPaper(Base):
    __tablename__ = "question_papers"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    file_path = Column(String, nullable=True)
    answer_file_path = Column(String, nullable=True)
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
    extracted_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    question = relationship("Question", back_populates="submissions")
    evaluation = relationship("Evaluation", back_populates="submission", uselist=False, cascade="all, delete-orphan")

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    marks_awarded = Column(Integer, nullable=False)
    max_marks = Column(Integer, nullable=False)
    detailed_scores = Column(JSON)  # Detailed scoring breakdown
    ai_feedback = Column(Text, nullable=False)
    manual_marks = Column(Integer, nullable=True)
    manual_feedback = Column(Text, nullable=True)
    is_manually_overridden = Column(Integer, default=0)
    evaluation_time = Column(Float, nullable=True)  # Time taken to evaluate in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    submission = relationship("Submission", back_populates="evaluation")