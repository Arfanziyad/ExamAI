import requests

def test_create_test():
    url = "http://localhost:8000/api/question-papers"
    test_data = {
        "title": "Sample Mathematics Test",
        "subject": "Mathematics",
        "description": "A test covering basic arithmetic and algebra",
        "question_text": """1. What is the value of 5 + 3 × 4?
2. Solve for x: 2x + 5 = 13
3. What is the area of a rectangle with length 6 units and width 4 units?""",
        "answer_text": """1. 17 (follow order of operations: multiplication first)
2. x = 4 (subtract 5 from both sides, then divide by 2)
3. 24 square units (multiply length by width: 6 × 4)"""
    }

    try:
        # Send POST request
        response = requests.post(url, data=test_data)
        
        # Print response details
        print("\nResponse Status:", response.status_code)
        print("\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
        
        print("\nResponse Body:")
        print(response.text)
        
        if response.status_code in (200, 201):
            print("\n✅ Test creation successful!")
            return True
        else:
            print(f"\n❌ Test creation failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    test_create_test()