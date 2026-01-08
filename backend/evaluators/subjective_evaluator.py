# evaluators/subjective_evaluator.py
from sentence_transformers import SentenceTransformer, util
import re
from typing import Dict, Any, List
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import Counter
import logging

class SubjectiveEvaluator:
    """Enhanced subjective answer evaluator with multiple evaluation strategies"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.semantic_model = SentenceTransformer('all-mpnet-base-v2')  # Better for semantic similarity
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        
        self.stop_words = set(stopwords.words('english'))
    
    def evaluate(self, question: str, student_answer: str, model_answer: str, subject_area: str = 'general') -> Dict[str, Any]:
        """Enhanced evaluation with multiple scoring approaches"""
        try:
            # Preprocessing
            if len(student_answer.strip()) < 5:
                return self._handle_insufficient_answer()
            
            # CASE 1: Check for completely unrelated/irrelevant answer → 0 marks
            if self._is_completely_unrelated(student_answer, model_answer, question):
                return self._handle_completely_unrelated_answer()
            
            # Check for simple irrelevant patterns
            if self._is_irrelevant_answer(student_answer):
                return self._handle_irrelevant_answer()
            
            # CASE 2: Check for exact or near-exact match → Full marks
            exact_match_result = self._check_exact_match(student_answer, model_answer)
            if exact_match_result['is_exact_match']:
                return self._handle_exact_match(exact_match_result['similarity'])
            
            # Multiple evaluation approaches for normal cases
            semantic_score = self._semantic_similarity_evaluation(student_answer, model_answer)
            keyword_score = self._keyword_based_evaluation(student_answer, model_answer, subject_area)
            structure_score = self._structure_evaluation(student_answer, model_answer)
            comprehensiveness_score = self._comprehensiveness_evaluation(student_answer, model_answer)
            
            # Weighted combination based on subject area
            weights = self._get_subject_weights(subject_area)
            
            final_score = (
                semantic_score['score'] * weights['semantic'] +
                keyword_score['score'] * weights['keyword'] +
                structure_score['score'] * weights['structure'] +
                comprehensiveness_score['score'] * weights['comprehensiveness']
            )
            
            # Generate detailed feedback
            all_feedback = {
                'semantic': semantic_score['feedback'],
                'keyword': keyword_score['feedback'],
                'structure': structure_score['feedback'],
                'comprehensiveness': comprehensiveness_score['feedback']
            }
            
            marks_awarded = self._score_to_marks(final_score)
            feedback = self._generate_comprehensive_feedback(final_score, all_feedback, subject_area)
            
            return {
                'similarity_score': round(final_score / 100, 3),
                'marks_awarded': marks_awarded,
                'feedback': feedback,
                'detailed_scores': {
                    'semantic': semantic_score['score'],
                    'keyword': keyword_score['score'],
                    'structure': structure_score['score'],
                    'comprehensiveness': comprehensiveness_score['score']
                },
                'subject_area': subject_area
            }
            
        except Exception as e:
            return {
                'similarity_score': 0.0,
                'marks_awarded': 0,
                'feedback': f"Evaluation error: {str(e)}",
                'detailed_scores': {'error': True},
                'subject_area': subject_area
            }
    
    def _semantic_similarity_evaluation(self, student_answer: str, model_answer: str) -> Dict[str, Any]:
        """Advanced semantic similarity using multiple models"""
        try:
            # Use both models for better coverage
            embeddings_base = self.model.encode([model_answer, student_answer], convert_to_tensor=True)
            embeddings_advanced = self.semantic_model.encode([model_answer, student_answer], convert_to_tensor=True)
            
            # Calculate similarities
            cosine_base = util.pytorch_cos_sim(embeddings_base[0], embeddings_base[1]).item()
            cosine_advanced = util.pytorch_cos_sim(embeddings_advanced[0], embeddings_advanced[1]).item()
            
            # Weighted average (advanced model gets more weight)
            final_similarity = (cosine_base * 0.3 + cosine_advanced * 0.7)
            
            # Convert to percentage and provide feedback
            score = final_similarity * 100
            
            if score >= 85:
                feedback = "Excellent semantic understanding - answer closely matches expected response"
            elif score >= 75:
                feedback = "Very good semantic understanding with minor variations"
            elif score >= 65:
                feedback = "Good understanding but missing some key concepts"
            elif score >= 50:
                feedback = "Basic understanding shown but lacks depth"
            else:
                feedback = "Limited understanding - consider reviewing core concepts"
            
            return {
                'score': score,
                'feedback': feedback,
                'raw_similarity': final_similarity
            }
            
        except Exception as e:
            return {
                'score': 50,
                'feedback': f"Could not compute semantic similarity: {str(e)}",
                'raw_similarity': 0.5
            }
    
    def _keyword_based_evaluation(self, student_answer: str, model_answer: str, subject_area: str) -> Dict[str, Any]:
        """Enhanced keyword matching with domain-specific weighting"""
        try:
            # Extract key terms from both answers
            student_keywords = self._extract_key_terms(student_answer, subject_area)
            model_keywords = self._extract_key_terms(model_answer, subject_area)
            
            if not model_keywords:
                return {'score': 70, 'feedback': 'Unable to extract key terms from model answer'}
            
            # Calculate keyword overlap
            common_keywords = set(student_keywords) & set(model_keywords)
            keyword_coverage = len(common_keywords) / len(model_keywords) if model_keywords else 0
            
            # Check for domain-specific terms
            domain_bonus = self._check_domain_terminology(student_answer, subject_area)
            
            # Calculate score
            base_score = keyword_coverage * 80
            bonus_score = domain_bonus * 20
            final_score = min(base_score + bonus_score, 100)
            
            # Generate feedback
            if keyword_coverage >= 0.8:
                feedback = f"Excellent use of key terminology ({len(common_keywords)}/{len(model_keywords)} key terms)"
            elif keyword_coverage >= 0.6:
                feedback = f"Good use of terminology ({len(common_keywords)}/{len(model_keywords)} key terms covered)"
            elif keyword_coverage >= 0.4:
                feedback = f"Some key terms present ({len(common_keywords)}/{len(model_keywords)}) but could be more comprehensive"
            else:
                feedback = f"Limited use of key terminology ({len(common_keywords)}/{len(model_keywords)} terms)"
            
            if domain_bonus > 0:
                feedback += " - includes relevant domain-specific language"
            
            return {
                'score': final_score,
                'feedback': feedback,
                'keywords_matched': list(common_keywords)
            }
            
        except Exception as e:
            return {
                'score': 50,
                'feedback': f"Keyword evaluation error: {str(e)}",
                'keywords_matched': []
            }
    
    def _extract_key_terms(self, text: str, subject_area: str) -> List[str]:
        """Extract key terms based on subject area"""
        # Clean and tokenize
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = word_tokenize(text_clean)
        
        # Remove stopwords and short words
        meaningful_words = [word for word in tokens 
                          if word not in self.stop_words and len(word) > 2]
        
        # Subject-specific term extraction
        if subject_area == 'science':
            # Prioritize scientific terms
            science_indicators = ['theory', 'hypothesis', 'experiment', 'analysis', 'reaction', 
                                'element', 'compound', 'organism', 'cell', 'energy']
            key_terms = [word for word in meaningful_words 
                        if any(indicator in word for indicator in science_indicators) or len(word) > 5]
        elif subject_area == 'math':
            # Mathematical terms
            math_indicators = ['equation', 'formula', 'variable', 'function', 'derivative', 
                             'integral', 'matrix', 'vector', 'proof', 'theorem']
            key_terms = [word for word in meaningful_words 
                        if any(indicator in word for indicator in math_indicators) or word.isalnum()]
        else:
            # General approach - use frequency and length
            word_freq = Counter(meaningful_words)
            key_terms = [word for word, freq in word_freq.most_common(20) if len(word) > 3]
        
        return key_terms
    
    def _check_domain_terminology(self, answer: str, subject_area: str) -> float:
        """Check for appropriate domain-specific terminology"""
        answer_lower = answer.lower()
        
        domain_terms = {
            'science': ['hypothesis', 'theory', 'experiment', 'observation', 'data', 'analysis', 
                       'conclusion', 'variable', 'control', 'methodology'],
            'math': ['equation', 'formula', 'proof', 'theorem', 'lemma', 'axiom', 'corollary', 
                    'derivative', 'integral', 'limit'],
            'humanities': ['analysis', 'interpretation', 'context', 'significance', 'perspective', 
                          'argument', 'evidence', 'thesis', 'critique'],
            'programming': ['algorithm', 'function', 'variable', 'loop', 'condition', 'array', 
                           'object', 'class', 'method', 'debugging']
        }
        
        if subject_area not in domain_terms:
            return 0.0
        
        relevant_terms = domain_terms[subject_area]
        found_terms = sum(1 for term in relevant_terms if term in answer_lower)
        
        return min(found_terms / len(relevant_terms), 1.0)
    
    def _structure_evaluation(self, student_answer: str, model_answer: str) -> Dict[str, Any]:
        """Evaluate the structure and organization of the answer"""
        try:
            student_sentences = sent_tokenize(student_answer)
            model_sentences = sent_tokenize(model_answer)
            
            # Structure metrics
            length_ratio = len(student_sentences) / max(len(model_sentences), 1)
            has_intro = self._has_introduction(student_answer)
            has_conclusion = self._has_conclusion(student_answer)
            has_transitions = self._has_transition_words(student_answer)
            
            # Scoring
            score = 60  # Base score
            
            # Length appropriateness
            if 0.7 <= length_ratio <= 1.5:
                score += 15
            elif 0.5 <= length_ratio <= 2.0:
                score += 10
            else:
                score += 5
            
            # Structure elements
            if has_intro:
                score += 10
            if has_conclusion:
                score += 10
            if has_transitions:
                score += 15
            
            # Generate feedback
            feedback_parts = []
            if has_intro and has_conclusion:
                feedback_parts.append("Well-structured with clear introduction and conclusion")
            elif has_intro or has_conclusion:
                feedback_parts.append("Good structure but could benefit from both intro and conclusion")
            else:
                feedback_parts.append("Consider adding introduction and conclusion for better structure")
            
            if has_transitions:
                feedback_parts.append("Good use of transition words")
            else:
                feedback_parts.append("Could improve flow with transition words")
            
            feedback = " - ".join(feedback_parts)
            
            return {
                'score': min(score, 100),
                'feedback': feedback
            }
            
        except Exception as e:
            return {
                'score': 70,
                'feedback': f"Structure evaluation error: {str(e)}"
            }
    
    def _has_introduction(self, text: str) -> bool:
        """Check if answer has an introduction"""
        first_sentence = sent_tokenize(text)[0] if sent_tokenize(text) else ""
        intro_indicators = ['firstly', 'to begin', 'initially', 'first', 'in this', 'this question', 'to answer']
        return any(indicator in first_sentence.lower() for indicator in intro_indicators)
    
    def _has_conclusion(self, text: str) -> bool:
        """Check if answer has a conclusion"""
        sentences = sent_tokenize(text)
        if not sentences:
            return False
        
        last_sentence = sentences[-1].lower()
        conclusion_indicators = ['therefore', 'thus', 'hence', 'in conclusion', 'to conclude', 
                               'finally', 'in summary', 'overall', 'consequently']
        return any(indicator in last_sentence for indicator in conclusion_indicators)
    
    def _has_transition_words(self, text: str) -> bool:
        """Check for transition words that improve flow"""
        transition_words = ['however', 'moreover', 'furthermore', 'additionally', 'nevertheless', 
                          'consequently', 'meanwhile', 'similarly', 'in contrast', 'on the other hand']
        text_lower = text.lower()
        return any(word in text_lower for word in transition_words)
    
    def _comprehensiveness_evaluation(self, student_answer: str, model_answer: str) -> Dict[str, Any]:
        """Evaluate how comprehensive the student answer is"""
        try:
            # Break down answers into concepts/topics
            student_concepts = self._extract_concepts(student_answer)
            model_concepts = self._extract_concepts(model_answer)
            
            if not model_concepts:
                return {'score': 70, 'feedback': 'Unable to evaluate comprehensiveness'}
            
            # Calculate concept coverage
            covered_concepts = set(student_concepts) & set(model_concepts)
            coverage_ratio = len(covered_concepts) / len(model_concepts)
            
            # Check for elaboration and examples
            has_examples = self._has_examples(student_answer)
            has_elaboration = self._has_elaboration(student_answer)
            
            # Calculate score
            base_score = coverage_ratio * 70
            example_bonus = 15 if has_examples else 0
            elaboration_bonus = 15 if has_elaboration else 0
            
            final_score = min(base_score + example_bonus + elaboration_bonus, 100)
            
            # Generate feedback
            feedback_parts = []
            if coverage_ratio >= 0.8:
                feedback_parts.append("Comprehensive coverage of key concepts")
            elif coverage_ratio >= 0.6:
                feedback_parts.append("Good coverage but missing some important points")
            else:
                feedback_parts.append("Limited coverage - consider addressing more key concepts")
            
            if has_examples:
                feedback_parts.append("includes relevant examples")
            if has_elaboration:
                feedback_parts.append("shows detailed explanation")
            
            feedback = " - ".join(feedback_parts)
            
            return {
                'score': final_score,
                'feedback': feedback,
                'coverage_ratio': coverage_ratio
            }
            
        except Exception as e:
            return {
                'score': 60,
                'feedback': f"Comprehensiveness evaluation error: {str(e)}",
                'coverage_ratio': 0.5
            }
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract main concepts from text"""
        # Split into sentences and extract noun phrases
        sentences = sent_tokenize(text)
        concepts = []
        
        for sentence in sentences:
            # Simple noun phrase extraction (can be enhanced with NLP libraries)
            words = word_tokenize(sentence.lower())
            # Look for important nouns and noun phrases
            for i, word in enumerate(words):
                if (len(word) > 4 and word not in self.stop_words and 
                    word.isalpha()):
                    concepts.append(word)
                    
                    # Check for compound concepts
                    if i < len(words) - 1 and words[i+1] not in self.stop_words:
                        compound = f"{word} {words[i+1]}"
                        if len(compound) > 8:
                            concepts.append(compound)
        
        return list(set(concepts))  # Remove duplicates
    
    def _has_examples(self, text: str) -> bool:
        """Check if answer includes examples"""
        example_indicators = ['for example', 'for instance', 'such as', 'like', 'including', 
                            'e.g.', 'i.e.', 'namely', 'specifically']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in example_indicators)
    
    def _has_elaboration(self, text: str) -> bool:
        """Check if answer shows detailed elaboration"""
        # Check for explanatory phrases
        elaboration_indicators = ['because', 'since', 'due to', 'as a result', 'this means', 
                                'in other words', 'that is', 'which indicates', 'this shows']
        text_lower = text.lower()
        elaboration_count = sum(1 for indicator in elaboration_indicators 
                              if indicator in text_lower)
        
        # Also check for sufficient detail (longer sentences, multiple clauses)
        sentences = sent_tokenize(text)
        detailed_sentences = [s for s in sentences if len(s.split()) > 15]
        
        return elaboration_count >= 2 or len(detailed_sentences) >= 2
    
    def _get_subject_weights(self, subject_area: str) -> Dict[str, float]:
        """Get evaluation weights based on subject area"""
        weight_profiles = {
            'science': {
                'semantic': 0.35,
                'keyword': 0.35,
                'structure': 0.15,
                'comprehensiveness': 0.15
            },
            'math': {
                'semantic': 0.30,
                'keyword': 0.40,
                'structure': 0.15,
                'comprehensiveness': 0.15
            },
            'humanities': {
                'semantic': 0.40,
                'keyword': 0.25,
                'structure': 0.20,
                'comprehensiveness': 0.15
            },
            'programming': {
                'semantic': 0.25,
                'keyword': 0.45,
                'structure': 0.15,
                'comprehensiveness': 0.15
            },
            'general': {
                'semantic': 0.35,
                'keyword': 0.30,
                'structure': 0.20,
                'comprehensiveness': 0.15
            }
        }
        
        return weight_profiles.get(subject_area, weight_profiles['general'])
    
    def _score_to_marks(self, score: float) -> int:
        """Convert percentage score to marks out of 10"""
        if score >= 95:
            return 10
        elif score >= 90:
            return 9
        elif score >= 85:
            return 8
        elif score >= 75:
            return 7
        elif score >= 65:
            return 6
        elif score >= 55:
            return 5
        elif score >= 45:
            return 4
        elif score >= 35:
            return 3
        elif score >= 25:
            return 2
        elif score >= 15:
            return 1
        else:
            return 0
    
    def _generate_comprehensive_feedback(self, final_score: float, all_feedback: Dict[str, str], 
                                       subject_area: str) -> str:
        """Generate detailed feedback combining all evaluation aspects"""
        feedback_parts = []
        
        # Overall assessment
        if final_score >= 90:
            feedback_parts.append("Outstanding answer! Demonstrates excellent understanding.")
        elif final_score >= 80:
            feedback_parts.append("Very good answer with strong understanding.")
        elif final_score >= 70:
            feedback_parts.append("Good answer showing solid grasp of concepts.")
        elif final_score >= 60:
            feedback_parts.append("Satisfactory answer but could be improved.")
        elif final_score >= 40:
            feedback_parts.append("Below average - needs significant improvement.")
        else:
            feedback_parts.append("Poor answer - requires major revision.")
        
        # Detailed breakdowns
        feedback_parts.append(f"\nDetailed Analysis:")
        feedback_parts.append(f"• Content Understanding: {all_feedback['semantic']}")
        feedback_parts.append(f"• Key Terms Usage: {all_feedback['keyword']}")
        feedback_parts.append(f"• Answer Structure: {all_feedback['structure']}")
        feedback_parts.append(f"• Completeness: {all_feedback['comprehensiveness']}")
        
        # Subject-specific suggestions
        suggestions = self._get_subject_suggestions(subject_area, final_score)
        if suggestions:
            feedback_parts.append(f"\nSuggestions for {subject_area.title()} Answers:")
            for suggestion in suggestions:
                feedback_parts.append(f"• {suggestion}")
        
        return "\n".join(feedback_parts)
    
    def _get_subject_suggestions(self, subject_area: str, score: float) -> List[str]:
        """Get subject-specific improvement suggestions"""
        if score >= 80:
            return []  # No suggestions needed for high scores
        
        suggestions_map = {
            'science': [
                "Include more scientific terminology and concepts",
                "Support claims with evidence or examples",
                "Explain cause-and-effect relationships clearly",
                "Reference scientific methods or principles"
            ],
            'math': [
                "Show more detailed step-by-step calculations",
                "Use precise mathematical language",
                "Include relevant formulas or theorems",
                "Verify your final answer"
            ],
            'humanities': [
                "Provide more analysis and interpretation",
                "Include relevant historical or cultural context",
                "Use specific examples to support arguments",
                "Consider multiple perspectives on the topic"
            ],
            'programming': [
                "Include more technical details about implementation",
                "Explain algorithmic thinking and logic",
                "Discuss efficiency and best practices",
                "Provide code examples if appropriate"
            ],
            'general': [
                "Provide more detailed explanations",
                "Use relevant examples to illustrate points",
                "Organize answer with clear structure",
                "Include conclusion that summarizes key points"
            ]
        }
        
        return suggestions_map.get(subject_area, suggestions_map['general'])
    
    def _handle_insufficient_answer(self) -> Dict[str, Any]:
        """Handle very short or empty answers"""
        return {
            'similarity_score': 0.0,
            'marks_awarded': 0,
            'feedback': "Answer too short or empty. Please provide a more detailed response with proper explanation.",
            'detailed_scores': {
                'semantic': 0,
                'keyword': 0,
                'structure': 0,
                'comprehensiveness': 0
            }
        }
    
    def _handle_irrelevant_answer(self) -> Dict[str, Any]:
        """Handle clearly irrelevant answers"""
        return {
            'similarity_score': 0.0,
            'marks_awarded': 0,
            'feedback': "Answer appears to be irrelevant or indicates lack of knowledge. Please provide a meaningful response related to the question.",
            'detailed_scores': {
                'semantic': 0,
                'keyword': 0,
                'structure': 0,
                'comprehensiveness': 0
            }
        }
    
    def _is_irrelevant_answer(self, answer: str) -> bool:
        """Check if answer is clearly irrelevant (simple pattern matching for obvious cases)"""
        # Only check if answer is very short (less than 20 chars) to avoid false positives
        if len(answer.strip()) > 20:
            return False
            
        irrelevant_patterns = [
            'i don\'t know', 'idk', 'no idea', 'dunno', 'not sure',
            'random text', 'test answer', 'hello world', 'nothing', 
            'no clue', 'dont know', 'i dunno'
        ]
        
        answer_lower = answer.lower().strip()
        
        # Must be an exact match or very close match for short answers
        for pattern in irrelevant_patterns:
            if answer_lower == pattern or answer_lower.startswith(pattern):
                return True
        
        return False
    
    def _is_completely_unrelated(self, student_answer: str, model_answer: str, question: str) -> bool:
        """
        Check if student answer is completely unrelated to the question/model answer.
        Uses semantic similarity to detect if answer is about a completely different topic.
        """
        try:
            # Encode all three texts
            embeddings = self.semantic_model.encode(
                [question, model_answer, student_answer], 
                convert_to_tensor=True
            )
            
            # Calculate similarity between student answer and question
            question_similarity = util.pytorch_cos_sim(embeddings[0], embeddings[2]).item()
            
            # Calculate similarity between student answer and model answer
            model_similarity = util.pytorch_cos_sim(embeddings[1], embeddings[2]).item()
            
            # If both similarities are extremely low, answer is unrelated
            # Threshold: less than 0.15 (15%) similarity indicates completely different topic
            unrelated_threshold = 0.15
            
            is_unrelated = (question_similarity < unrelated_threshold and 
                          model_similarity < unrelated_threshold)
            
            if is_unrelated:
                logger = logging.getLogger(__name__)
                logger.info(f"Detected unrelated answer - Q_sim: {question_similarity:.3f}, M_sim: {model_similarity:.3f}")
            
            return is_unrelated
            
        except Exception as e:
            # If error in checking, don't mark as unrelated
            return False
    
    def _check_exact_match(self, student_answer: str, model_answer: str) -> Dict[str, Any]:
        """
        Check if student answer is an exact or near-exact match with model answer.
        Returns dict with is_exact_match flag and similarity score.
        """
        try:
            # Normalize both answers for comparison
            student_normalized = self._normalize_text(student_answer)
            model_normalized = self._normalize_text(model_answer)
            
            # Check for exact text match (after normalization)
            if student_normalized == model_normalized:
                return {'is_exact_match': True, 'similarity': 1.0}
            
            # Check semantic similarity for near-exact matches
            embeddings = self.semantic_model.encode(
                [model_answer, student_answer], 
                convert_to_tensor=True
            )
            similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
            
            # Threshold: 0.92 or higher indicates near-exact match (slightly lower for paraphrasing)
            exact_match_threshold = 0.92
            
            if similarity >= exact_match_threshold:
                logger = logging.getLogger(__name__)
                logger.info(f"Detected exact/near-exact match - Similarity: {similarity:.3f}")
                return {'is_exact_match': True, 'similarity': similarity}
            
            return {'is_exact_match': False, 'similarity': similarity}
            
        except Exception as e:
            return {'is_exact_match': False, 'similarity': 0.0}
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison by removing punctuation, extra spaces, and lowercasing"""
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def _handle_completely_unrelated_answer(self) -> Dict[str, Any]:
        """Handle completely unrelated answers - award 0 marks"""
        return {
            'similarity_score': 0.0,
            'marks_awarded': 0,
            'feedback': "The answer provided is completely unrelated to the question asked. It appears to be about a different topic entirely. Please read the question carefully and provide a relevant response.",
            'detailed_scores': {
                'semantic': 0,
                'keyword': 0,
                'structure': 0,
                'comprehensiveness': 0,
                'unrelated_answer': True
            }
        }
    
    def _handle_exact_match(self, similarity: float) -> Dict[str, Any]:
        """Handle exact or near-exact matches - award full marks"""
        return {
            'similarity_score': 1.0,
            'marks_awarded': 10,
            'feedback': "Excellent! Your answer matches the model answer perfectly. You have demonstrated complete understanding of the concept with accurate and comprehensive coverage of all key points.",
            'detailed_scores': {
                'semantic': 100,
                'keyword': 100,
                'structure': 100,
                'comprehensiveness': 100,
                'exact_match': True,
                'match_similarity': round(similarity * 100, 2)
            }
        }