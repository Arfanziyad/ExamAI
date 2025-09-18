import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_create_question_paper():
    """Test creating a question paper"""
    url = "http://localhost:8000/api/question-papers"
    data = {
        "title": "Test Question Paper",
        "subject": "Test Subject",
        "description": "Test Description",
        "question_text": "What is the capital of France?\nWhat is the largest planet in our solar system?",
        "answer_text": "Paris\nJupiter"
    }
    try:
        response = requests.post(url, data=data)
        logger.info(f"Create Question Paper Response: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        return response.status_code == 200 or response.status_code == 201
    except Exception as e:
        logger.error(f"Error creating question paper: {str(e)}")
        return False

def test_get_question_papers():
    """Test retrieving question papers"""
    url = "http://localhost:8000/api/question-papers"
    try:
        response = requests.get(url)
        logger.info(f"Get Question Papers Response: {response.status_code}")
        logger.info(f"Found {len(response.json())} question papers")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error getting question papers: {str(e)}")
        return False

def run_tests():
    """Run all tests"""
    logger.info("Starting API tests...")
    
    # Test creating a question paper
    logger.info("\nTesting create question paper endpoint...")
    if test_create_question_paper():
        logger.info("✓ Create question paper test passed")
    else:
        logger.error("✗ Create question paper test failed")
    
    # Add a small delay between tests
    time.sleep(1)
    
    # Test getting question papers
    logger.info("\nTesting get question papers endpoint...")
    if test_get_question_papers():
        logger.info("✓ Get question papers test passed")
    else:
        logger.error("✗ Get question papers test failed")

if __name__ == "__main__":
    run_tests()