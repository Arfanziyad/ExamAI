"""
Migration script to add flexible answer ordering support to submissions table
"""

import sqlite3
import os
import logging
from database import DATABASE_URL

logger = logging.getLogger(__name__)

def migrate_submissions_table():
    """Add flexible answer ordering columns to the submissions table"""
    
    # Extract database path from DATABASE_URL
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
    else:
        raise ValueError("This migration script only supports SQLite databases")
    
    if not os.path.exists(db_path):
        logger.warning(f"Database file {db_path} does not exist. No migration needed.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(submissions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'answer_sequence' not in columns:
            migrations_needed.append("ALTER TABLE submissions ADD COLUMN answer_sequence JSON")
            
        if 'answer_sections' not in columns:
            migrations_needed.append("ALTER TABLE submissions ADD COLUMN answer_sections JSON")
            
        if 'sequence_confidence' not in columns:
            migrations_needed.append("ALTER TABLE submissions ADD COLUMN sequence_confidence REAL DEFAULT 1.0")
        
        if migrations_needed:
            logger.info(f"Running {len(migrations_needed)} migrations for answer sequence support...")
            
            for migration in migrations_needed:
                logger.info(f"Executing: {migration}")
                cursor.execute(migration)
            
            conn.commit()
            logger.info("Answer sequence migration completed successfully!")
        else:
            logger.info("No migrations needed. Submissions table is already up to date.")
            
    except sqlite3.Error as e:
        logger.error(f"Database migration failed: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_submissions_table()