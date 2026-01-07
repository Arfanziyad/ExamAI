import time
import logging
from typing import Dict, Any, Optional
from evaluators.subjective_evaluator import SubjectiveEvaluator
from evaluators.coding_evaluator import CodingEvaluator
from sqlalchemy.orm import Session
from models import Submission, QuestionPaper, Question, AnswerScheme, Evaluation
from .answer_sequence_service import analyze_answer_sequence

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
        then performs the evaluation using the appropriate evaluator based on question type.
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

            # Check if this question is part of an OR group and mark as attempted
            if getattr(question, 'or_group_id', None):
                await self._mark_or_group_attempt(db, question, str(getattr(submission, 'student_name', '')))

            # Get the question paper for context
            question_paper = db.query(QuestionPaper).filter(QuestionPaper.id == question.question_paper_id).first()
            if not question_paper:
                raise ValueError(f"Question paper not found for question {question.id}")
            
            # Extract values from SQLAlchemy objects
            question_text = str(getattr(question, 'question_text', ''))
            answer_text = str(getattr(question_paper, 'answer_text', ''))
            subject_area = str(getattr(question, 'subject_area', 'general'))
            question_type = str(getattr(question, 'question_type', 'subjective'))
            max_marks = int(getattr(question, 'max_marks', 10))
            
            # Get answer scheme if available
            answer_scheme = db.query(AnswerScheme).filter(AnswerScheme.question_id == question.id).first()
            model_answer = str(getattr(answer_scheme, 'model_answer', answer_text)) if answer_scheme else answer_text
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
    
    async def _mark_or_group_attempt(self, db: Session, attempted_question: Question, student_name: str):
        """
        Mark questions in OR group as attempted/not attempted based on student submission
        """
        try:
            if not getattr(attempted_question, 'or_group_id', None):
                return
            
            # Get all questions in the same OR group for this question paper
            or_group_questions = db.query(Question).filter(
                Question.question_paper_id == attempted_question.question_paper_id,
                Question.or_group_id == attempted_question.or_group_id
            ).all()
            
            # Check which questions this student has submitted for
            for question in or_group_questions:
                # Check if student has submission for this question
                submission_exists = db.query(Submission).filter(
                    Submission.question_id == question.id,
                    Submission.student_name == student_name,
                    Submission.extracted_text.isnot(None),
                    Submission.extracted_text != ''
                ).first()
                
                # Update attempt status
                if submission_exists:
                    # Use SQLAlchemy update for the is_attempted field
                    db.query(Question).filter(Question.id == question.id).update({'is_attempted': 1})
                    logger.info(f"Marked question {question.id} as attempted for OR group {getattr(attempted_question, 'or_group_id', '')}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error marking OR group attempt: {str(e)}")

    async def get_or_group_evaluation_summary(self, db: Session, question_paper_id: int, student_name: str) -> Dict[str, Any]:
        """
        Get evaluation summary for OR groups showing which questions were attempted
        """
        try:
            # Get all questions for this question paper
            questions = db.query(Question).filter(
                Question.question_paper_id == question_paper_id
            ).all()
            
            # Group questions by OR group
            or_groups = {}
            standalone_questions = []
            
            for question in questions:
                if getattr(question, 'or_group_id', None):
                    if question.or_group_id not in or_groups:
                        or_groups[question.or_group_id] = {
                            'title': getattr(question, 'or_group_title', f'OR Group {question.or_group_id}'),
                            'questions': [],
                            'attempted_questions': [],
                            'total_possible_marks': 0,
                            'earned_marks': 0
                        }
                    
                    or_groups[question.or_group_id]['questions'].append(question)
                    or_groups[question.or_group_id]['total_possible_marks'] += question.max_marks
                    
                    # Check if this question was attempted by the student
                    submission = db.query(Submission).filter(
                        Submission.question_id == question.id,
                        Submission.student_name == student_name
                    ).first()
                    
                    if submission and getattr(submission, 'extracted_text', None):
                        or_groups[question.or_group_id]['attempted_questions'].append(question)
                        
                        # Get evaluation for this submission
                        evaluation = db.query(Evaluation).filter(
                            Evaluation.submission_id == submission.id
                        ).first()
                        
                        if evaluation:
                            or_groups[question.or_group_id]['earned_marks'] += evaluation.marks_awarded
                else:
                    standalone_questions.append(question)
            
            return {
                'or_groups': or_groups,
                'standalone_questions': standalone_questions
            }
            
        except Exception as e:
            logger.error(f"Error getting OR group summary: {str(e)}")
            return {'or_groups': {}, 'standalone_questions': []}

    async def evaluate_submission_with_sequence_analysis(
        self,
        db: Session,
        submission_id: int,
        force_reanalysis: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate submission with flexible answer sequence analysis
        Handles cases where students answer questions in any order
        """
        try:
            # Get submission with related data
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")
            
            extracted_text = str(getattr(submission, 'extracted_text', ''))
            if not extracted_text.strip():
                raise ValueError(f"No extracted text available for submission {submission_id}")
            
            # Get question and question paper
            question = db.query(Question).filter(Question.id == submission.question_id).first()
            if not question:
                raise ValueError(f"Question {submission.question_id} not found")
            
            question_paper = db.query(QuestionPaper).filter(QuestionPaper.id == question.question_paper_id).first()
            if not question_paper:
                raise ValueError(f"Question paper not found")
            
            # Get all questions for this question paper for sequence analysis
            all_questions = db.query(Question).filter(
                Question.question_paper_id == question.question_paper_id
            ).all()
            
            # Prepare expected questions for sequence analysis
            expected_questions = []
            for q in all_questions:
                expected_questions.append({
                    'question_number': q.question_number,
                    'question_text': str(getattr(q, 'question_text', '')),
                    'max_marks': int(getattr(q, 'max_marks', 10)),
                    'question_type': str(getattr(q, 'question_type', 'subjective')),
                    'question_id': q.id
                })
            
            # Perform sequence analysis if not done or if forced
            sequence_analysis = getattr(submission, 'answer_sections', None)
            if not sequence_analysis or force_reanalysis:
                sequence_analysis = analyze_answer_sequence(extracted_text, expected_questions)
                
                # Update submission with sequence analysis results
                submission.answer_sequence = sequence_analysis.get('answer_sequence', [])
                submission.answer_sections = sequence_analysis.get('answer_sections', [])
                submission.sequence_confidence = sequence_analysis.get('sequence_confidence', 1.0)
                db.commit()
            
            # Extract the specific answer for this question
            question_answer = self._extract_question_answer(
                sequence_analysis, question, extracted_text
            )
            
            # Check OR groups
            if getattr(question, 'or_group_id', None):
                await self._mark_or_group_attempt(db, question, str(submission.student_name))
            
            # Get model answer and evaluate
            answer_scheme = db.query(AnswerScheme).filter(AnswerScheme.question_id == question.id).first()
            model_answer = str(getattr(answer_scheme, 'model_answer', '')) if answer_scheme else str(getattr(question_paper, 'answer_text', ''))
            
            # Evaluate the extracted answer for this specific question
            evaluation_result = await self.evaluate_answer(
                question_text=str(getattr(question, 'question_text', '')),
                student_answer=question_answer,
                model_answer=model_answer,
                subject_area=str(getattr(question, 'subject_area', 'general')),
                question_type=str(getattr(question, 'question_type', 'subjective')),
                max_marks=int(getattr(question, 'max_marks', 10))
            )
            
            # Add sequence analysis metadata
            evaluation_result['sequence_analysis'] = {
                'detected_sequence': sequence_analysis.get('answer_sequence', []),
                'sequence_confidence': sequence_analysis.get('sequence_confidence', 1.0),
                'total_sections_found': len(sequence_analysis.get('answer_sections', [])),
                'question_specific_answer': len(question_answer.strip()) > 0
            }
            
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
            
            # Save evaluation
            if not getattr(evaluation, 'id', None):
                db.add(evaluation)
            db.commit()
            
            logger.info(f"Sequence-aware evaluation completed for submission {submission_id}")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Sequence-aware evaluation failed: {str(e)}")
            q_max_marks = int(getattr(question, 'max_marks', 10)) if 'question' in locals() else 10
            return self._fallback_evaluation(q_max_marks, str(e))

    def _extract_question_answer(
        self, 
        sequence_analysis: Dict[str, Any], 
        question: Question, 
        full_text: str
    ) -> str:
        """
        Extract the answer for a specific question from the sequence analysis
        """
        if not sequence_analysis or not sequence_analysis.get('parsed_answers'):
            return full_text  # Fallback to full text
        
        parsed_answers = sequence_analysis['parsed_answers']
        question_number = str(question.question_number)
        
        # Try exact question number match
        if question_number in parsed_answers:
            return parsed_answers[question_number]
        
        # Try with sub-questions
        for key, answer in parsed_answers.items():
            if key.startswith(f"{question_number}_"):
                return answer
        
        # Try content-based matching
        content_match_key = f"{question_number}_content_match"
        if content_match_key in parsed_answers:
            return parsed_answers[content_match_key]
        
        # If no specific match found, return a relevant section or full text
        answer_sections = sequence_analysis.get('answer_sections', [])
        for section in answer_sections:
            if section.get('question_number') == question_number:
                return section.get('content', '')
        
        # Fallback to full text
        logger.warning(f"Could not extract specific answer for question {question_number}, using full text")
        return full_text