"""Clear all test data from the database"""
from database import get_db
from models import QuestionPaper, Question, AnswerScheme, Submission, Evaluation

def clear_all_data():
    """Delete all records from all tables"""
    db = next(get_db())
    try:
        # Delete in correct order (children first, then parents)
        print("Clearing database...")
        
        # Delete evaluations
        evaluations_count = db.query(Evaluation).count()
        db.query(Evaluation).delete()
        print(f"✓ Deleted {evaluations_count} evaluations")
        
        # Delete submissions
        submissions_count = db.query(Submission).count()
        db.query(Submission).delete()
        print(f"✓ Deleted {submissions_count} submissions")
        
        # Delete answer schemes
        answer_schemes_count = db.query(AnswerScheme).count()
        db.query(AnswerScheme).delete()
        print(f"✓ Deleted {answer_schemes_count} answer schemes")
        
        # Delete questions
        questions_count = db.query(Question).count()
        db.query(Question).delete()
        print(f"✓ Deleted {questions_count} questions")
        
        # Delete question papers
        papers_count = db.query(QuestionPaper).count()
        db.query(QuestionPaper).delete()
        print(f"✓ Deleted {papers_count} question papers")
        
        # Commit all changes
        db.commit()
        print("\n✅ Database cleared successfully!")
        print(f"\nTotal records deleted: {evaluations_count + submissions_count + answer_schemes_count + questions_count + papers_count}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error clearing database: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    response = input("⚠️  This will delete ALL data from the database. Are you sure? (yes/no): ")
    if response.lower() == 'yes':
        clear_all_data()
    else:
        print("Operation cancelled.")
