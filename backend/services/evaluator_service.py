import time
import logging
from typing import Dict, Any
from evaluators.subjective_evaluator import SubjectiveEvaluator

logger = logging.getLogger(__name__)

class EvaluatorService:
    def __init__(self):
        self.evaluator = SubjectiveEvaluator()
        logger.info("EvaluatorService initialized with SubjectiveEvaluator")
    
    async def evaluate_answer(
        self, 
        question_text: str, 
        student_answer: str, 
        model_answer: str, 
        subject_area: str = 'general',
        max_marks: int = 10
    ) -> Dict[str, Any]:
        """
        Evaluate student answer using the enhanced subjective evaluator
        """
        try:
            start_time = time.time()
            
            # Log evaluation start
            logger.info(f"Starting evaluation for subject: {subject_area}")
            logger.debug(f"Question length: {len(question_text)}, Student answer length: {len(student_answer)}")
            
            # Use your enhanced evaluator
            evaluation_result = self.evaluator.evaluate(
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