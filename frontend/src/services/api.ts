const API_BASE_URL = 'http://localhost:5000';

export interface OCRResult {
  file_path: string;
  extracted_text: string;
  confidence: number;
}

export async function uploadQuestions(
  questionText: string,
  answerText: string,
  title = 'Untitled Test',
  subject = 'general',
  description = ''
): Promise<{
  id: string;
}> {
  const formData = new FormData();
  formData.append('question_text', questionText);
  formData.append('answer_text', answerText);
  formData.append('title', title);
  formData.append('subject', subject);
  if (description) formData.append('description', description);

  const response = await fetch(`${API_BASE_URL}/api/question-papers`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to create question paper: ${response.status} ${text}`);
  }

  const result = await response.json();
  return { id: result.id };
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

interface EvaluationResult {
  similarity_score: number;
  marks_awarded: number;
  max_marks: number;
  detailed_scores: Record<string, number>;
  ai_feedback: string;
  evaluation_time: string;
}

interface SubmissionResponse {
  id: number;
  student_name: string;
  handwriting_image_path: string;
  extracted_text?: string;
  ocr_confidence?: number;
  evaluation?: EvaluationResult;
}

// Submit answer and receive evaluation
export async function submitAnswer(formData: FormData): Promise<SubmissionResponse> {
  try {
    // Submit the answer - now with integrated OCR and evaluation
    const response = await fetch(`${API_BASE_URL}/api/questions/${formData.get('question_id')}/submissions`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Failed to submit answer: ${response.status} ${text}`);
    }

    const submission = await response.json();

    // Check if evaluation is already included in the response
    if (submission.evaluation) {
      return submission;
    }

    // If no evaluation yet, wait and try to get it
    console.log('Waiting for OCR and evaluation processing...');
    
    // Wait for processing to complete (OCR + evaluation)
    await new Promise(resolve => setTimeout(resolve, 3000));

    try {
      // Try to get evaluation results
      const evaluationResponse = await fetch(`${API_BASE_URL}/api/submissions/${submission.id}/evaluation`);

      if (evaluationResponse.ok) {
        const evaluationData = await evaluationResponse.json();
        return { 
          ...submission, 
          evaluation: {
            similarity_score: evaluationData.similarity_score,
            marks_awarded: evaluationData.marks_awarded,
            max_marks: evaluationData.max_marks,
            detailed_scores: evaluationData.detailed_scores,
            ai_feedback: evaluationData.ai_feedback,
            evaluation_time: evaluationData.evaluation_time
          }
        };
      } else {
        console.warn('Evaluation not ready yet');
        return submission;
      }
    } catch (evalError) {
      console.warn('Could not fetch evaluation:', evalError);
      return submission;
    }
  } catch (error) {
    console.error('Submission error:', error);
    throw error;
  }
}

export async function getEvaluationResults(answerId: string | number): Promise<EvaluationResult> {
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
