"""
Lightweight fallback SubjectiveEvaluator

This evaluator provides a simple, dependency-free evaluation so the backend
can run without heavy ML packages. It implements the same public methods
used by EvaluatorService: evaluate(), get_evaluation_criteria(), validate_inputs().
"""

import re
from typing import Dict, Any, List


class SubjectiveEvaluator:
    def __init__(self):
        # Lightweight evaluator does not require external models
        self.use_embeddings = False

    def evaluate(self, question: str, student_answer: str, model_answer: str, subject_area: str = 'general') -> Dict[str, Any]:
        # Basic validations
        if not student_answer or len(student_answer.strip()) < 5:
            return self._handle_insufficient_answer()

        # Simple keyword overlap as proxy for similarity
        student_tokens = self._tokenize(student_answer)
        model_tokens = self._tokenize(model_answer)

        if not model_tokens:
            semantic_score = 50.0
        else:
            common = set(student_tokens) & set(model_tokens)
            semantic_score = (len(common) / max(len(model_tokens), 1)) * 100

        keyword_score = semantic_score  # reuse as heuristic

        # Structure: compare sentence counts
        student_sentences = self._sentences(student_answer)
        model_sentences = self._sentences(model_answer)
        if model_sentences:
            length_ratio = len(student_sentences) / max(len(model_sentences), 1)
            structure_score = max(30, min(100, int(60 * (1 - abs(1 - length_ratio)) + 40)))
        else:
            structure_score = 60

        # Comprehensiveness: coverage of model tokens
        covered = len(set(student_tokens) & set(model_tokens))
        comprehensiveness = (covered / max(len(model_tokens), 1)) * 100

        # Weights (keep similar to original defaults)
        weights = self._get_subject_weights(subject_area)
        final_score = (
            semantic_score * weights['semantic'] +
            keyword_score * weights['keyword'] +
            structure_score * weights['structure'] +
            comprehensiveness * weights['comprehensiveness']
        )

        marks_awarded = self._score_to_marks(final_score)

        return {
            'similarity_score': round(final_score / 100, 3),
            'marks_awarded': marks_awarded,
            'max_marks': 10,
            'detailed_scores': {
                'semantic': round(semantic_score, 2),
                'keyword': round(keyword_score, 2),
                'structure': round(structure_score, 2),
                'comprehensiveness': round(comprehensiveness, 2)
            },
            'feedback': 'This is a lightweight evaluation (no ML models available).',
            'evaluation_time': 0.0,
            'subject_area': subject_area
        }

    def get_evaluation_criteria(self, subject_area: str) -> Dict[str, Any]:
        return {
            'semantic_weight': 0.35,
            'keyword_weight': 0.30,
            'structure_weight': 0.20,
            'comprehensiveness_weight': 0.15,
            'description': 'Fallback lightweight criteria'
        }

    def validate_inputs(self, question: str, student_answer: str, model_answer: str) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not question or not question.strip():
            errors.append('Question text cannot be empty')
        if not student_answer or not student_answer.strip():
            errors.append('Student answer cannot be empty')
        if not model_answer or not model_answer.strip():
            warnings.append('Model answer is empty or short')

        return {'is_valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}

    # --- helper utilities ---
    def _tokenize(self, text: str) -> List[str]:
        text_clean = re.sub(r"[^\w\s]", ' ', (text or '').lower())
        tokens = [t for t in text_clean.split() if len(t) > 2]
        return tokens

    def _sentences(self, text: str) -> List[str]:
        # naive sentence split
        return [s.strip() for s in re.split(r'[\.!?]+', text) if s.strip()]

    def _get_subject_weights(self, subject_area: str) -> Dict[str, float]:
        profiles = {
            'science': {'semantic': 0.35, 'keyword': 0.35, 'structure': 0.15, 'comprehensiveness': 0.15},
            'math': {'semantic': 0.30, 'keyword': 0.40, 'structure': 0.15, 'comprehensiveness': 0.15},
            'humanities': {'semantic': 0.40, 'keyword': 0.25, 'structure': 0.20, 'comprehensiveness': 0.15},
            'programming': {'semantic': 0.25, 'keyword': 0.45, 'structure': 0.15, 'comprehensiveness': 0.15},
            'general': {'semantic': 0.35, 'keyword': 0.30, 'structure': 0.20, 'comprehensiveness': 0.15}
        }
        return profiles.get(subject_area, profiles['general'])

    def _score_to_marks(self, score: float) -> int:
        # map 0-100 to 0-10
        return max(0, min(10, int(round(score / 10))))

    def _handle_insufficient_answer(self) -> Dict[str, Any]:
        return {
            'similarity_score': 0.0,
            'marks_awarded': 0,
            'feedback': 'Answer too short or empty. Please provide more detail.',
            'detailed_scores': {'semantic': 0, 'keyword': 0, 'structure': 0, 'comprehensiveness': 0},
            'max_marks': 10,
            'evaluation_time': 0.0
        }