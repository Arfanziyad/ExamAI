import requests
import os

# Test the submission endpoint
url = 'http://127.0.0.1:5000/api/questions/10/submissions'
files = {'file': ('student_answer.jpg', open('c:\Projects\AI_simple_final\temp_student_answer.jpg', 'rb'), 'image/jpeg')}
data = {'student_name': 'Alex Johnson (Integration Test)'}

print('Sending student submission...')
try:
    response = requests.post(url, files=files, data=data, timeout=60)
    print(f'Status Code: {response.status_code}')
    if response.status_code == 201:
        print('SUCCESS: Student submission processed!')
        result = response.json()
        print(f'Submission ID: {result.get("id")}')
        print(f'Extracted Text: {result.get("extracted_text", "N/A")[:100]}...')
        print(f'OCR Confidence: {result.get("ocr_confidence", "N/A")}')
        if result.get('evaluation'):
            eval_data = result['evaluation']
            print(f'Marks Awarded: {eval_data.get("marks_awarded")}/{eval_data.get("max_marks")}')
            print(f'AI Feedback: {eval_data.get("ai_feedback", "N/A")[:150]}...')
    else:
        print(f'ERROR: {response.text}')
except Exception as e:
    print(f'Exception: {e}')
finally:
    files['file'][1].close()
