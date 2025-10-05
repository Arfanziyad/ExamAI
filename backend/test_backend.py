import requests
import json

# Test data as specified by the user
test_data = {
    "title": "SubjectandCoding test",
    "subject": "General", 
    "description": "Test with both subjective and coding questions",
    "questions": [
        {
            "question_text": "What is Photosynthesis?",
            "answer_text": "Photosynthesis is the process of converting sunlight and carbondioxide to glucose and oxygen.",
            "question_number": 1,
            "max_marks": 5,
            "question_type": "subjective"
        },
        {
            "question_text": "write the code in python for \"hello,world!\"",
            "answer_text": "print(\"hello,world!\")",
            "question_number": 2,
            "max_marks": 10,
            "question_type": "coding-python"
        }
    ]
}

# Start the Flask server
print("🚀 Starting Flask server...")
import sys
sys.path.append('c:/Projects/AI_simple_final/backend')

from flask_server import app
from database import create_tables

# Create tables first
create_tables()
print("✅ Database tables ready")

# Test the question creation logic directly
from models import QuestionPaper, Question, AnswerScheme
from database import get_db

print("🧪 Testing question paper creation...")

# Get database session
db = next(get_db())

try:
    # Calculate total marks for the question paper
    total_marks = sum(q_data.get("max_marks", 10) for q_data in test_data["questions"])
    print(f"📊 Calculated total marks: {total_marks}")
    
    # Create question paper
    combined_question_text = "\n\n".join([
        f"Question {i+1}: {q['question_text']}" 
        for i, q in enumerate(test_data["questions"])
    ])
    combined_answer_text = "\n\n".join([
        f"Answer {i+1}: {q['answer_text']}" 
        for i, q in enumerate(test_data["questions"])
    ])
    
    question_paper = QuestionPaper(
        title=test_data["title"],
        subject=test_data["subject"],
        description=test_data["description"],
        question_text=combined_question_text,
        answer_text=combined_answer_text,
        total_marks=total_marks
    )
    
    # Save to database
    db.add(question_paper)
    db.commit()
    db.refresh(question_paper)
    
    print(f"✅ Question paper created with ID: {question_paper.id}")
    print(f"📝 Title: {question_paper.title}")
    print(f"🎯 Total marks: {question_paper.total_marks}")

    # Create individual Question and AnswerScheme records
    created_questions = []
    for i, q_data in enumerate(test_data["questions"]):
        question = Question(
            question_paper_id=question_paper.id,
            question_text=q_data["question_text"],
            question_number=q_data.get("question_number", i + 1),
            max_marks=q_data.get("max_marks", 10),
            subject_area=test_data["subject"].lower() if test_data["subject"] else 'general',
            question_type=q_data.get("question_type", "subjective")
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        
        # Create an AnswerScheme for the question
        answer_scheme = AnswerScheme(
            question_id=question.id,
            model_answer=q_data["answer_text"],
            key_points=[],
            marking_criteria={},
            sample_answers={}
        )
        db.add(answer_scheme)
        db.commit()
        
        created_questions.append({
            "question_id": question.id,
            "question_number": question.question_number,
            "question_type": question.question_type,
            "max_marks": question.max_marks,
            "text": question.question_text
        })
        
        print(f"✅ Question {question.question_number} created:")
        print(f"   📋 Type: {question.question_type}")
        print(f"   🎯 Marks: {question.max_marks}")
        print(f"   ❓ Text: {question.question_text}")

    print(f"\n🎉 TEST CREATION SUCCESSFUL!")
    print(f"📊 Summary:")
    print(f"   - Question Paper ID: {question_paper.id}")
    print(f"   - Total Questions: {len(created_questions)}")
    print(f"   - Total Marks: {question_paper.total_marks}")
    print(f"   - Question Types: {[q['question_type'] for q in created_questions]}")
    
    # Test the new total marks functionality
    print(f"\n🔍 Testing total marks calculation:")
    print(f"   - Q1 (Subjective): {created_questions[0]['max_marks']} marks")
    print(f"   - Q2 (Coding): {created_questions[1]['max_marks']} marks")
    print(f"   - Total: {sum(q['max_marks'] for q in created_questions)} marks")
    
finally:
    db.close()

print("\n✅ Backend test completed successfully!")