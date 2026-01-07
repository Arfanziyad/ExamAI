#!/usr/bin/env python3
"""
Migration script to add sub-question support and migrate Complete_QP_1 to proper sub-questions
"""

import sqlite3
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_complete_qp1_to_subquestions(cursor):
    """Migrate Complete_QP_1 to have proper sub-questions (1a, 1b, 2a, 3a, 3b, 4a)"""
    logger.info("Migrating Complete_QP_1 to sub-questions...")
    
    # Find Complete_QP_1 paper
    cursor.execute("SELECT id FROM question_papers WHERE title = 'Complete_QP_1' AND subject = 'Basic'")
    paper = cursor.fetchone()
    
    if not paper:
        logger.warning("Complete_QP_1 not found, skipping sub-question migration")
        return
    
    paper_id = paper[0]
    logger.info(f"Found Complete_QP_1 with ID: {paper_id}")
    
    # Check if questions already exist for this paper
    cursor.execute("SELECT COUNT(*) FROM questions WHERE question_paper_id = ?", (paper_id,))
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        logger.info(f"Complete_QP_1 already has {existing_count} questions, skipping migration")
        return
    
    # Define the correct sub-questions as per the actual question paper
    sub_questions = [
        {
            "main_num": 1, "sub": "a", 
            "text": "What is the chemical formula for water?",
            "answer": "H₂O - It means that each water molecule has 2 hydrogen atoms and 1 oxygen atom",
            "marks": 5
        },
        {
            "main_num": 1, "sub": "b", 
            "text": "What gas do plants release during photosynthesis?",
            "answer": "Oxygen - Plants make food using sunlight and release oxygen as a by-product.",
            "marks": 5
        },
        {
            "main_num": 2, "sub": "a", 
            "text": "What is the smallest unit of life?",
            "answer": "Cell - All living organisms are made up of cells, which are the basic building blocks of life.",
            "marks": 5
        },
        {
            "main_num": 3, "sub": "a", 
            "text": "What is the center of an atom called?",
            "answer": "Nucleus - It contains protons and neutrons and holds most of the atom's mass.",
            "marks": 5
        },
        {
            "main_num": 3, "sub": "b", 
            "text": "Which planet is known as the Red Planet?",
            "answer": "Mars - It appears red due to iron oxide (rust) on its surface.",
            "marks": 5
        },
        {
            "main_num": 4, "sub": "a", 
            "text": "What is the process of liquid turning into gas?",
            "answer": "Evaporation - It happens when molecules gain enough heat to escape into the air.",
            "marks": 5
        }
    ]
    
    # Insert each sub-question and its answer scheme
    for i, q in enumerate(sub_questions, 1):
        # Insert question
        cursor.execute("""
            INSERT INTO questions (
                question_paper_id, question_number, main_question_number, sub_question,
                question_text, max_marks, question_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_id, i, q["main_num"], q["sub"],
            q["text"], q["marks"], "subjective"
        ))
        
        # Get the question ID
        question_id = cursor.lastrowid
        
        # Insert answer scheme
        cursor.execute("""
            INSERT INTO answer_schemes (
                question_id, model_answer, key_points, marking_criteria
            ) VALUES (?, ?, ?, ?)
        """, (
            question_id, q["answer"], '[]', '[]'
        ))
        
        logger.info(f"Added question {q['main_num']}{q['sub']}: {q['text'][:50]}...")
    
    logger.info(f"Successfully migrated Complete_QP_1 with {len(sub_questions)} sub-questions")

def migrate_database():
    """Add sub-question columns, remove or_group_title, and migrate Complete_QP_1"""
    
    # Database path
    backend_dir = Path(__file__).parent
    db_path = backend_dir / "app.db"
    
    if not db_path.exists():
        logger.warning(f"Database not found at {db_path}. Creating new database.")
        return
    
    # Create backup
    backup_path = backend_dir / "exam_ai_backup_sub_questions.db"
    if backup_path.exists():
        logger.info("Backup already exists, skipping backup creation")
    else:
        logger.info(f"Creating backup: {backup_path}")
        import shutil
        shutil.copy2(db_path, backup_path)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(questions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"Current questions table columns: {column_names}")
        
        # Add sub-question support columns if they don't exist
        if 'main_question_number' not in column_names:
            logger.info("Adding main_question_number column...")
            cursor.execute("""
                ALTER TABLE questions 
                ADD COLUMN main_question_number INTEGER NULL
            """)
            
        if 'sub_question' not in column_names:
            logger.info("Adding sub_question column...")
            cursor.execute("""
                ALTER TABLE questions 
                ADD COLUMN sub_question TEXT NULL
            """)
        
        # Populate main_question_number for existing questions (non-sub-questions)
        logger.info("Updating main_question_number for existing questions...")
        cursor.execute("""
            UPDATE questions 
            SET main_question_number = question_number 
            WHERE main_question_number IS NULL AND sub_question IS NULL
        """)
        
        # Remove or_group_title column if it exists
        if 'or_group_title' in column_names:
            logger.info("Removing or_group_title column...")
            # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
            
            # Get all data
            cursor.execute("SELECT * FROM questions")
            questions_data = cursor.fetchall()
            
            # Get column info excluding or_group_title
            new_columns = [col for col in columns if col[1] != 'or_group_title']
            
            # Create temporary table
            column_defs = []
            for col in new_columns:
                col_name, col_type, not_null, default_val, primary_key = col[1], col[2], col[3], col[4], col[5]
                col_def = f"{col_name} {col_type}"
                if not_null:
                    col_def += " NOT NULL"
                if default_val is not None:
                    col_def += f" DEFAULT {default_val}"
                if primary_key:
                    col_def += " PRIMARY KEY"
                column_defs.append(col_def)
            
            # Add the new columns to the definition
            if 'main_question_number' not in column_names:
                column_defs.append("main_question_number INTEGER NULL")
            if 'sub_question' not in column_names:
                column_defs.append("sub_question TEXT NULL")
                
            create_table_sql = f"CREATE TABLE questions_new ({', '.join(column_defs)})"
            logger.info(f"Creating new table: {create_table_sql}")
            cursor.execute(create_table_sql)
            
            # Copy data (excluding or_group_title)
            old_column_names = [col[1] for col in columns]
            new_column_names = [col for col in old_column_names if col != 'or_group_title']
            
            # Add new columns if they weren't in the original
            if 'main_question_number' not in old_column_names:
                new_column_names.append('main_question_number')
            if 'sub_question' not in old_column_names:
                new_column_names.append('sub_question')
                
            placeholders = ', '.join(['?' for _ in new_column_names])
            insert_sql = f"INSERT INTO questions_new ({', '.join(new_column_names)}) VALUES ({placeholders})"
            
            # Prepare data for insertion
            or_group_title_index = old_column_names.index('or_group_title') if 'or_group_title' in old_column_names else None
            
            new_data = []
            for row in questions_data:
                # Remove or_group_title from row
                if or_group_title_index is not None:
                    row = list(row)
                    row.pop(or_group_title_index)
                
                # Add main_question_number and sub_question if they weren't in original
                if 'main_question_number' not in old_column_names:
                    row = list(row) + [row[old_column_names.index('question_number')]]  # Use question_number as main_question_number
                if 'sub_question' not in old_column_names:
                    row = list(row) + [None]  # sub_question is NULL for existing questions
                    
                new_data.append(row)
            
            cursor.executemany(insert_sql, new_data)
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE questions")
            cursor.execute("ALTER TABLE questions_new RENAME TO questions")
            
            logger.info("Successfully removed or_group_title column")
        
        # Commit changes
        conn.commit()
        logger.info("Sub-question migration completed successfully!")
        
        # Now migrate Complete_QP_1 to sub-questions
        migrate_complete_qp1_to_subquestions(cursor)
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(questions)")
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        logger.info(f"Updated questions table columns: {new_column_names}")
        
        # Show Complete_QP_1 questions
        cursor.execute("""
            SELECT qp.title, q.main_question_number, q.sub_question, q.question_text 
            FROM questions q 
            JOIN question_papers qp ON q.question_paper_id = qp.id 
            WHERE qp.title = 'Complete_QP_1' AND qp.subject = 'Basic'
            ORDER BY q.main_question_number, q.sub_question
        """)
        complete_qp1_questions = cursor.fetchall()
        logger.info(f"Complete_QP_1 questions after migration:")
        for q in complete_qp1_questions:
            logger.info(f"  {q[1]}{q[2]}: {q[3][:50]}...")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()