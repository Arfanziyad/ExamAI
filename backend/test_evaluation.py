import sys
import asyncio
sys.path.append('c:/Projects/AI_simple_final/backend')

from flask_server import app
from database import get_db
from models import QuestionPaper, Question, Submission, Evaluation, AnswerScheme
from services.evaluator_service import EvaluatorService
import json

async def test_evaluation():
    print("🧪 TESTING STUDENT EVALUATION SYSTEM")
    print("=" * 50)

    # Student answers as provided by user
    student_answers = {
        1: "Photosynthesis is the process of converting sunlight and carbondioxide to glucose and oxygen",
        2: 'print("hello,world!")'
    }

    print("📝 Student Answers:")
    print(f"   Q1 (Subjective): {student_answers[1]}")
    print(f"   Q2 (Coding): {student_answers[2]}")
    print()

    # Get database session
    db = next(get_db())

    try:
        # Find the most recent question paper (should be our test paper)
        question_paper = db.query(QuestionPaper).order_by(QuestionPaper.id.desc()).first()
        
        if not question_paper:
            print("❌ No question paper found! Please run test_backend.py first.")
            return
        
        print(f"📊 Testing Question Paper: '{question_paper.title}' (ID: {question_paper.id})")
        print(f"🎯 Total Marks Available: {question_paper.total_marks}")
        print()
        
        # Get all questions for this paper
        questions = db.query(Question).filter_by(question_paper_id=question_paper.id).order_by(Question.question_number).all()
        
        if len(questions) != 2:
            print(f"❌ Expected 2 questions, found {len(questions)}")
            return
        
        print("📋 Questions Found:")
        for q in questions:
            print(f"   Q{q.question_number}: {q.question_type} ({q.max_marks} marks)")
            print(f"      Text: {q.question_text[:50]}...")
        print()
        
        # Initialize evaluator service
        evaluator_service = EvaluatorService()
        
        # Track evaluation results
        evaluation_results = []
        total_marks_earned = 0
        
        print("🔍 EVALUATING EACH QUESTION:")
        print("-" * 40)
        
        # Evaluate each question
        for question in questions:
            question_num = getattr(question, 'question_number')
            student_answer = student_answers.get(question_num, "")
            
            print(f"\n📝 Question {question_num} ({question.question_type}):")
            print(f"   Max Marks: {question.max_marks}")
            print(f"   Question: {question.question_text}")
            print(f"   Student Answer: {student_answer}")
            
            # Get model answer from answer scheme
            answer_scheme = db.query(AnswerScheme).filter_by(question_id=question.id).first()
            model_answer = str(answer_scheme.model_answer) if answer_scheme else "No model answer found"
            
            print(f"   Model Answer: {model_answer}")
            
            # Evaluate the answer using the async method
            try:
                result = await evaluator_service.evaluate_answer(
                    question_text=str(question.question_text),
                    student_answer=student_answer,
                    model_answer=model_answer,
                    subject_area=str(getattr(question, 'subject_area', 'general')),
                    question_type=str(question.question_type),
                    max_marks=getattr(question, 'max_marks')
                )
                
                marks_earned = result['marks_awarded']
                similarity = result['similarity_score']
                
                print(f"   ✅ EVALUATION RESULT:")
                print(f"      Similarity Score: {similarity:.2%}")
                print(f"      Marks Awarded: {marks_earned}/{question.max_marks}")
                print(f"      Percentage: {(marks_earned/question.max_marks)*100:.1f}%")
                
                if 'detailed_scores' in result and result['detailed_scores']:
                    print(f"      Detailed Scores: {result['detailed_scores']}")
                
                if result.get('ai_feedback'):
                    feedback = result['ai_feedback'][:100] + "..." if len(result['ai_feedback']) > 100 else result['ai_feedback']
                    print(f"      AI Feedback: {feedback}")
                
                evaluation_results.append({
                    'question_number': question_num,
                    'question_type': str(question.question_type),
                    'max_marks': getattr(question, 'max_marks'),
                    'marks_earned': marks_earned,
                    'similarity': similarity,
                    'result': result
                })
                
                total_marks_earned += marks_earned
                
            except Exception as e:
                print(f"   ❌ Evaluation failed: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 50)
        print("📊 FINAL EVALUATION SUMMARY")
        print("=" * 50)
        
        print(f"📝 Question Paper: {question_paper.title}")
        print(f"👤 Student: Test Student")
        print()
        
        print("📋 Individual Question Results:")
        for result in evaluation_results:
            percentage = (result['marks_earned'] / result['max_marks']) * 100
            print(f"   Q{result['question_number']} ({result['question_type']}): "
                  f"{result['marks_earned']}/{result['max_marks']} marks ({percentage:.1f}%)")
        
        print()
        print(f"🎯 TOTAL SCORE:")
        total_max_marks = getattr(question_paper, 'total_marks')
        print(f"   Marks Earned: {total_marks_earned}/{total_max_marks}")
        total_percentage = (total_marks_earned/total_max_marks)*100
        print(f"   Percentage: {total_percentage:.1f}%")
        
        print("\n🎉 EVALUATION TEST COMPLETED SUCCESSFULLY!")
        
        # Show grade breakdown
        if total_percentage >= 90:
            grade = "A+"
        elif total_percentage >= 80:
            grade = "A"
        elif total_percentage >= 70:
            grade = "B"
        elif total_percentage >= 60:
            grade = "C"
        elif total_percentage >= 50:
            grade = "D"
        else:
            grade = "F"
        
        print(f"\n🏆 FINAL GRADE: {grade} ({total_percentage:.1f}%)")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

# Run the async test
if __name__ == "__main__":
    asyncio.run(test_evaluation())