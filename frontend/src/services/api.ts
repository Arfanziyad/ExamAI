const API_BASE_URL = 'http://localhost:8000';

export interface OCRResult {
  file_path: string;
  extracted_text: string;
  confidence: number;
}

export async function uploadQuestions(
  questionFile: File,
  modelAnswerFile: File,
  title = 'Untitled Test',
  subject = 'general',
  description = ''
): Promise<{
  id: string;
  questionOCR: OCRResult;
  answerOCR: OCRResult;
}> {
  const formData = new FormData();
  formData.append('file', questionFile);
  formData.append('answer_file', modelAnswerFile);
  formData.append('title', title);
  formData.append('subject', subject);
  if (description) formData.append('description', description);

  const response = await fetch(`${API_BASE_URL}/api/question-papers`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to upload questions: ${response.status} ${text}`);
  }

  return response.json();
}

export async function verifyOCRText(
  paperId: string,
  type: 'question' | 'model_answer',
  correctedText: string
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/question-papers/${paperId}/ocr-verify`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      type,
      corrected_text: correctedText,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to verify OCR text: ${response.status} ${text}`);
  }
}

// Option 1: submitAnswer accepts only FormData
export async function submitAnswer(formData: FormData): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/submissions`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to submit answer: ${response.status} ${text}`);
  }

  return response.json();
}

export async function getEvaluationResults(answerId: string | number) {
  const response = await fetch(`${API_BASE_URL}/api/submissions/${answerId}/evaluation`);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to get evaluation results: ${response.status} ${text}`);
  }

  return response.json();
}

export async function getTests() {
  const response = await fetch(`${API_BASE_URL}/api/question-papers`);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to get tests: ${response.status} ${text}`);
  }

  return response.json();
}

export async function getAllEvaluationResults() {
  const response = await fetch(`${API_BASE_URL}/api/submissions`);
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to fetch all evaluation results: ${response.status} ${text}`);
  }

  return response.json();
}
