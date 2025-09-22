import requests
import os
import sys

# Test the submission endpoint
url = 'http://127.0.0.1:5000/api/questions/10/submissions'
image_path = 'temp_student_answer.jpg'

print('=== STEP 2: STUDENT SUBMISSION TEST ===')
print(f'Uploading: {image_path}')
print(f'To endpoint: {url}')
print(f'Student: Alex Johnson (Integration Test)')
print()

try:
    with open(image_path, 'rb') as f:
        files = {'file': ('student_answer.jpg', f, 'image/jpeg')}
        data = {'student_name': 'Alex Johnson (Integration Test)'}
        
        print('Sending request... (This may take 30-60 seconds for OCR + Evaluation)')
        response = requests.post(url, files=files, data=data, timeout=120)
        
        print(f'Response Status: {response.status_code}')
        
        if response.status_code == 201:
            print('✅ SUCCESS: Student submission processed!')
            result = response.json()
            
            print('\n=== SUBMISSION RESULTS ===')
            print(f'Submission ID: {result.get("id")}')
            print(f'Question ID: {result.get("question_id")}')
            print(f'Student Name: {result.get("student_name")}')
            print(f'Submitted At: {result.get("submitted_at")}')
            
            print('\n=== OCR RESULTS ===')
            extracted_text = result.get("extracted_text", "N/A")
            print(f'Extracted Text: {extracted_text}')
            print(f'OCR Confidence: {result.get("ocr_confidence", "N/A")}')
            
            print('\n=== EVALUATION RESULTS ===')
            if result.get('evaluation'):
                eval_data = result['evaluation']
                print(f'Marks Awarded: {eval_data.get("marks_awarded")}/{eval_data.get("max_marks")}')
                print(f'Similarity Score: {eval_data.get("similarity_score", "N/A")}')
                print(f'Evaluation Time: {eval_data.get("evaluation_time", "N/A")} seconds')
                print(f'AI Feedback: {eval_data.get("ai_feedback", "N/A")}')
                print(f'Detailed Scores: {eval_data.get("detailed_scores", {})}')
                print('\n✅ INTEGRATION TEST COMPLETED SUCCESSFULLY!')
            else:
                print('⚠️  Evaluation not included in response (may be processing)')
        else:
            print(f'❌ ERROR: {response.status_code}')
            print(f'Response: {response.text}')
            
except FileNotFoundError:
    print(f'❌ ERROR: Image file not found: {image_path}')
except requests.exceptions.Timeout:
    print('❌ ERROR: Request timed out (OCR/Evaluation may take longer)')
except requests.exceptions.ConnectionError:
    print('❌ ERROR: Cannot connect to Flask server. Is it running on port 5000?')
except Exception as e:
    print(f'❌ ERROR: {e}')
    import traceback
    traceback.print_exc()