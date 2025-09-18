import requests

def test_create_question_paper():
    url = "http://localhost:8000/api/question-papers"
    data = {
        "title": "Sample Math Test",
        "subject": "Mathematics",
        "description": "Basic arithmetic test",
        "question_text": "What is 5 + 7?",
        "answer_text": "12"
    }
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_create_question_paper()