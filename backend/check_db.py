import sys
sys.path.append('c:/Projects/AI_simple_final/backend')
from database import get_db
from models import Question, QuestionPaper

db = next(get_db())
questions = db.query(Question).all()
papers = db.query(QuestionPaper).all()

print('Question Papers:')
for p in papers[-5:]:  # Last 5 papers
    print(f'  Paper {p.id}: {p.title}')

print('\nQuestions:')
for q in questions[-10:]:  # Last 10 questions
    print(f'  Question {q.id}: Paper {q.question_paper_id}, Q{q.question_number}, Type: {q.question_type}')

# Get questions for our latest paper
if papers:
    latest_paper = papers[-1]
    paper_questions = db.query(Question).filter(Question.question_paper_id == latest_paper.id).all()
    print(f'\nQuestions for Paper {latest_paper.id} ({latest_paper.title}):')
    for q in paper_questions:
        print(f'  Question {q.id}: Q{q.question_number}, Type: {q.question_type}')

db.close()