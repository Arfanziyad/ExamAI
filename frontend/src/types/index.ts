// Backend-compatible interfaces
export interface QuestionPaper {
  id: number;
  question_id: number;  // The associated Question ID for submissions
  title: string;
  subject: string;
  description: string;
  question_text: string;
  answer_text: string;
  created_at: string;
}

export interface Question {
  id: number;
  question_paper_id: number;
  question_text: string;
  question_number: number;
  max_marks: number;
  subject_area: string;
}

export interface SubmissionData {
  id: number;
  question_id: number;
  student_name: string;
  handwriting_image_path: string;
  extracted_text?: string;
  ocr_confidence?: number;
  submitted_at: string;
  evaluation?: EvaluationData;
}

export interface EvaluationData {
  id: number;
  similarity_score: number;
  marks_awarded: number;
  max_marks: number;
  detailed_scores: Record<string, number>;
  ai_feedback: string;
  evaluation_time: string;
  created_at: string;
}

export interface EvaluationResult {
  submission_id: number;
  student_name: string;
  similarity_score: number;
  marks_awarded: number;
  max_marks: number;
  detailed_scores: Record<string, number>;
  ai_feedback: string;
  evaluation_time: string;
  created_at: string;
  submitted_at: string;
}

// API Response interfaces
export interface SubmissionResponse {
  id: number;
  student_name: string;
  handwriting_image_path: string;
  extracted_text?: string;
  ocr_confidence?: number;
  evaluation?: EvaluationResult;
}

export interface OCRVerificationRequest {
  type: 'question' | 'model_answer';
  corrected_text: string;
}

// Legacy interfaces for backward compatibility (deprecated)
/** @deprecated Use QuestionPaper instead */
export interface Test {
  id: string;
  title: string;
  questions: Question[];
  createdAt: string;
}

/** @deprecated Use SubmissionData instead */
export interface Answer {
  id: string;
  questionId: string;
  imagePath: string;
  score?: number;
  feedback?: string;
}
