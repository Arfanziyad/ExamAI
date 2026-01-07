"""
Migration script to add OR groups support to existing database
This script adds the new columns needed for OR questions functionality
"""

import sqlite3
import os
import logging
from database import DATABASE_URL

logger = logging.getLogger(__name__)

def migrate_database():
    """Add OR groups columns to the questions table"""
    
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
        cursor.execute("PRAGMA table_info(questions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'or_group_id' not in columns:
            migrations_needed.append("ALTER TABLE questions ADD COLUMN or_group_id VARCHAR(50)")
            
        if 'or_group_title' not in columns:
            migrations_needed.append("ALTER TABLE questions ADD COLUMN or_group_title VARCHAR(200)")
            
        if 'is_attempted' not in columns:
            migrations_needed.append("ALTER TABLE questions ADD COLUMN is_attempted INTEGER DEFAULT 0")
        
        if migrations_needed:
            logger.info(f"Running {len(migrations_needed)} migrations...")
            
            for migration in migrations_needed:
                logger.info(f"Executing: {migration}")
                cursor.execute(migration)
            
            conn.commit()
            logger.info("Migration completed successfully!")
        else:
            logger.info("No migrations needed. Database is already up to date.")
            
    except sqlite3.Error as e:
        logger.error(f"Database migration failed: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_database()