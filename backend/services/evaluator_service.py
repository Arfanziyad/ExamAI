import time
import logging
from typing import Dict, Any, Optional
from evaluators.subjective_evaluator import SubjectiveEvaluator
from evaluators.coding_evaluator import CodingEvaluator
from sqlalchemy.orm import Session
from models import Submission, QuestionPaper, Question, AnswerScheme, Evaluation

logger = logging.getLogger(__name__)

class EvaluatorService:
    def __init__(self):
        self.subjective_evaluator = SubjectiveEvaluator()
        self.coding_evaluator = CodingEvaluator()
        logger.info("EvaluatorService initialized with both SubjectiveEvaluator and CodingEvaluator")
    
    async def evaluate_submission_with_ocr(
        self, 
        db: Session,
        submission_id: int
    ) -> Dict[str, Any]:
        """
        Evaluate a submission after OCR processing.
        This method fetches the submission, its associated question, and model answer,
        then performs the evaluation.
        """
        try:
            # Get the submission
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")
                
            extracted_text = getattr(submission, 'extracted_text', None)
            if not extracted_text:
                raise ValueError(f"No OCR text found for submission {submission_id}")

            # Get the question and its model answer
            question = db.query(Question).filter(Question.id == submission.question_id).first()
            if not question:
                raise ValueError(f"Question not found for submission {submission_id}")

            # Get the question paper for context
            question_paper = db.query(QuestionPaper).filter(QuestionPaper.id == question.question_paper_id).first()
            if not question_paper:
                raise ValueError(f"Question paper not found for question {question.id}")
            
            # Extract values from SQLAlchemy objects
            question_text = str(getattr(question_paper, 'question_text', ''))
            answer_text = str(getattr(question_paper, 'answer_text', ''))
            subject_area = str(getattr(question, 'subject_area', 'general'))
            question_type = str(getattr(question, 'question_type', 'subjective'))
            max_marks = int(getattr(question, 'max_marks', 10))
            
            # Evaluate against model answer
            evaluation_result = await self.evaluate_answer(
                question_text=question_text,
                student_answer=extracted_text,
                model_answer=answer_text,
                subject_area=subject_area,
                question_type=question_type,
                max_marks=max_marks
            )

            # Create or update evaluation record
            evaluation = Evaluation(
                submission_id=submission_id,
                similarity_score=evaluation_result['similarity_score'],
                marks_awarded=evaluation_result['marks_awarded'],
                max_marks=evaluation_result['max_marks'],
                detailed_scores=evaluation_result['detailed_scores'],
                ai_feedback=evaluation_result['ai_feedback'],
                evaluation_time=evaluation_result['evaluation_time']
            )
            
            db.add(evaluation)
            db.commit()

            return evaluation_result

        except Exception as e:
            logger.error(f"Evaluation failed for submission {submission_id}: {str(e)}")
            return self._fallback_evaluation(10, str(e))

    async def evaluate_submission(
        self,
        db: Session,
        submission_id: int
    ) -> Dict[str, Any]:
        """
        Evaluate a submission against its associated question's model answer
        """
        try:
            # Get the submission and related data
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")

            # Extract submission text
            extracted_text = getattr(submission, 'extracted_text', None)
            if not extracted_text:
                raise ValueError(f"No OCR text found for submission {submission_id}")

            # Get the question and its model answer
            question = db.query(Question).filter(Question.id == submission.question_id).first()
            if not question:
                raise ValueError(f"Question {submission.question_id} not found")

            answer_scheme = db.query(AnswerScheme).filter(AnswerScheme.question_id == question.id).first()
            if not answer_scheme:
                raise ValueError(f"Answer scheme for question {question.id} not found")

            # Get the question paper for context
            question_paper = db.query(QuestionPaper).filter(QuestionPaper.id == question.question_paper_id).first()
            if not question_paper:
                raise ValueError(f"Question paper {question.question_paper_id} not found")

            # Extract values from SQLAlchemy objects
            question_text = str(getattr(question_paper, 'question_text', ''))
            model_answer = str(getattr(answer_scheme, 'model_answer', ''))
            subject_area = str(getattr(question, 'subject_area', 'general'))
            max_marks = int(getattr(question, 'max_marks', 10))

            # Evaluate the submission
            evaluation_result = await self.evaluate_answer(
                question_text=question_text,
                student_answer=extracted_text,
                model_answer=model_answer,
                subject_area=subject_area,
                max_marks=max_marks
            )

            # Create or update evaluation record
            evaluation = db.query(Evaluation).filter(Evaluation.submission_id == submission_id).first()
            if not evaluation:
                evaluation = Evaluation(submission_id=submission_id)

            # Update evaluation fields
            for field, value in {
                'similarity_score': evaluation_result['similarity_score'],
                'marks_awarded': evaluation_result['marks_awarded'],
                'max_marks': evaluation_result['max_marks'],
                'detailed_scores': evaluation_result['detailed_scores'],
                'ai_feedback': evaluation_result['ai_feedback'],
                'evaluation_time': evaluation_result['evaluation_time']
            }.items():
                setattr(evaluation, field, value)

            # Save to database
            eval_id = getattr(evaluation, 'id', None)
            if not eval_id:
                db.add(evaluation)
            db.commit()

            return evaluation_result

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            q_max_marks = int(getattr(question, 'max_marks', 10)) if question else 10
            return self._fallback_evaluation(q_max_marks, str(e))
    
    async def evaluate_answer(
        self, 
        question_text: str, 
        student_answer: str, 
        model_answer: str, 
        subject_area: str = 'general',
        question_type: str = 'subjective',
        max_marks: int = 10
    ) -> Dict[str, Any]:
        """
        Evaluate student answer using the appropriate evaluator based on question type
        """
        try:
            start_time = time.time()
            
            # Log evaluation start
            logger.info(f"Starting evaluation for question type: {question_type}, subject: {subject_area}")
            logger.debug(f"Question length: {len(question_text)}, Student answer length: {len(student_answer)}")
            
            # Choose the appropriate evaluator
            if question_type == 'coding-python':
                evaluation_result = self.coding_evaluator.evaluate(
                    question=question_text,
                    student_answer=student_answer,
                    model_answer=model_answer
                )
            else:
                # Default to subjective evaluation
                evaluation_result = self.subjective_evaluator.evaluate(
                    question=question_text,
                    student_answer=student_answer,
                    model_answer=model_answer,
                    subject_area=subject_area
                )
            
            # Calculate evaluation time
            evaluation_time = time.time() - start_time
            
            # Scale marks to match max_marks
            original_marks = evaluation_result.get('marks_awarded', 0)
            scaled_marks = min(int((original_marks / 10) * max_marks), max_marks)
            
            # Prepare final result
            final_result = {
                'similarity_score': evaluation_result.get('similarity_score', 0.0),
                'marks_awarded': scaled_marks,
                'max_marks': max_marks,
                'detailed_scores': evaluation_result.get('detailed_scores', {}),
                'ai_feedback': evaluation_result.get('feedback', 'No feedback available'),
                'subject_area': evaluation_result.get('subject_area', subject_area),
                'evaluation_time': evaluation_time,
                'original_marks_out_of_10': original_marks
            }
            
            logger.info(f"Evaluation completed. Score: {scaled_marks}/{max_marks}, Time: {evaluation_time:.2f}s")
            return final_result
            
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            # Return fallback evaluation
            return self._fallback_evaluation(max_marks, str(e))
    
    def _fallback_evaluation(self, max_marks: int, error_message: str) -> Dict[str, Any]:
        """
        Fallback evaluation when the main evaluator fails
        """
        return {
            'similarity_score': 0.0,
            'marks_awarded': 0,
            'max_marks': max_marks,
            'detailed_scores': {
                'semantic': 0,
                'keyword': 0,
                'structure': 0,
                'comprehensiveness': 0,
                'error': True
            },
            'ai_feedback': f"Evaluation failed: {error_message}. Please try again or contact support.",
            'subject_area': 'general',
            'evaluation_time': 0.0,
            'original_marks_out_of_10': 0
        }
    
    def get_evaluation_criteria(self, subject_area: str) -> Dict[str, Any]:
        """
        Get evaluation criteria for a specific subject area
        """
        criteria = {
            'general': {
                'semantic_weight': 0.35,
                'keyword_weight': 0.30,
                'structure_weight': 0.20,
                'comprehensiveness_weight': 0.15,
                'description': 'Balanced evaluation focusing on understanding and expression'
            },
            'science': {
                'semantic_weight': 0.35,
                'keyword_weight': 0.35,
                'structure_weight': 0.15,
                'comprehensiveness_weight': 0.15,
                'description': 'Emphasizes scientific concepts and terminology'
            },
            'math': {
                'semantic_weight': 0.30,
                'keyword_weight': 0.40,
                'structure_weight': 0.15,
                'comprehensiveness_weight': 0.15,
                'description': 'Focuses on mathematical accuracy and proper notation'
            },
            'humanities': {
                'semantic_weight': 0.40,
                'keyword_weight': 0.25,
                'structure_weight': 0.20,
                'comprehensiveness_weight': 0.15,
                'description': 'Values analytical thinking and structured argumentation'
            },
            'programming': {
                'semantic_weight': 0.25,
                'keyword_weight': 0.45,
                'structure_weight': 0.15,
                'comprehensiveness_weight': 0.15,
                'description': 'Emphasizes technical accuracy and implementation details'
            }
        }
        
        return criteria.get(subject_area, criteria['general'])
    
    def validate_inputs(self, question: str, student_answer: str, model_answer: str) -> Dict[str, Any]:
        """
        Validate inputs before evaluation
        """
        errors = []
        warnings = []
        
        # Check for empty inputs
        if not question.strip():
            errors.append("Question text cannot be empty")
        
        if not student_answer.strip():
            errors.append("Student answer cannot be empty")
        
        if not model_answer.strip():
            errors.append("Model answer cannot be empty")
        
        # Check lengths
        if len(student_answer.strip()) < 10:
            warnings.append("Student answer is very short, evaluation may not be accurate")
        
        if len(model_answer.strip()) < 20:
            warnings.append("Model answer is short, consider providing more detail")
        
        # Check for obvious issues
        if student_answer.lower().strip() in ['i don\'t know', 'no idea', 'idk', 'nothing']:
            warnings.append("Student answer indicates lack of knowledge")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }