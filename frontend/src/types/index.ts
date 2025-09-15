export interface Test {
  id: string;
  title: string;
  questions: Question[];
  createdAt: string;
}

export interface Question {
  id: string;
  text: string;
  scheme: string;
  maxScore: number;
}

export interface Answer {
  id: string;
  questionId: string;
  imagePath: string;
  score?: number;
  feedback?: string;
}

export interface EvaluationResult {
  answerId: string;
  score: number;
  feedback: string;
  questionId: string;
}
