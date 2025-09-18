from database import engine, create_tables, get_db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_database_connection():
    try:
        # Test database connection
        logger.info("Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            
        # Test table creation
        logger.info("Testing table creation...")
        create_tables()
        logger.info("Tables created successfully")
        
        # Test session creation
        logger.info("Testing session creation...")
        db = next(get_db())
        logger.info("Session created successfully")
        db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_database_connection()