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
  question_type?: string;
  // Sub-question support
  main_question_number?: number;
  sub_question?: string;
  // OR Groups Support
  or_group_id?: string;
  is_attempted?: number;
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
  // Flexible Answer Ordering Support
  answer_sequence?: string[];
  answer_sections?: AnswerSection[];
  sequence_confidence?: number;
}

export interface AnswerSection {
  question_number: string;
  sub_question?: string;
  content: string;
  position_in_text: number;
  confidence: number;
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

// OR Groups interfaces
export interface ORGroup {
  id: string;
  title: string;
  questions: Question[];
  attempted_questions: Question[];
  total_possible_marks: number;
  earned_marks: number;
}

export interface ORGroupSummary {
  or_groups: Record<string, ORGroup>;
  standalone_questions: Question[];
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
