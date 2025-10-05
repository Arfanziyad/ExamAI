import sqlite3
import os

# Check if database exists and add the missing columns
db_path = 'app.db'

print("🔍 Checking database structure...")

if os.path.exists(db_path):
    print(f"✅ Database found at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fix question_papers table
    cursor.execute('PRAGMA table_info(question_papers);')
    qp_columns = [col[1] for col in cursor.fetchall()]
    
    print(f"📋 QuestionPaper columns: {qp_columns}")
    
    if 'total_marks' not in qp_columns:
        print('🔧 Adding total_marks column to question_papers table...')
        cursor.execute('ALTER TABLE question_papers ADD COLUMN total_marks INTEGER DEFAULT 0;')
        conn.commit()
        print('✅ total_marks column added to question_papers')
    else:
        print('✅ total_marks column already exists in question_papers')
    
    # Fix questions table  
    cursor.execute('PRAGMA table_info(questions);')
    q_columns = [col[1] for col in cursor.fetchall()]
    
    print(f"📋 Questions columns: {q_columns}")
    
    if 'question_type' not in q_columns:
        print('🔧 Adding question_type column to questions table...')
        cursor.execute('ALTER TABLE questions ADD COLUMN question_type VARCHAR DEFAULT "subjective";')
        conn.commit()
        print('✅ question_type column added to questions')
    else:
        print('✅ question_type column already exists in questions')
    
    # Show updated table structures
    print('📊 Updated question_papers table structure:')
    cursor.execute('PRAGMA table_info(question_papers);')
    for col in cursor.fetchall():
        print(f'  - {col[1]} ({col[2]})')
    
    print('📊 Updated questions table structure:')
    cursor.execute('PRAGMA table_info(questions);')
    for col in cursor.fetchall():
        print(f'  - {col[1]} ({col[2]})')
    
    conn.close()
else:
    print('❌ Database does not exist')
    # Create fresh database
    from database import create_tables
    create_tables()
    print('✅ Fresh database created with all tables')

print("🎯 Database setup complete!")