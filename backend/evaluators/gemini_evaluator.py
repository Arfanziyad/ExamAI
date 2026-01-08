# evaluators/gemini_evaluator.py
import os
import json
import logging
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-genai not installed. Gemini evaluation will be disabled.")

class GeminiEvaluator:
    """
    LLM-based evaluator using Google's Gemini API for nuanced answer evaluation.
    Provides deep contextual understanding and detailed feedback.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini evaluator.
        
        Args:
            api_key: Google API key. If None, will try to get from GEMINI_API_KEY env variable.
        """
        self.enabled = False
        self.client = None
        
        if not GEMINI_AVAILABLE:
            logger.warning("Gemini evaluator disabled: google-genai package not installed")
            return
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            logger.warning("Gemini evaluator disabled: No API key provided. Set GEMINI_API_KEY environment variable.")
            return
        
        try:
            # Configure Gemini client
            self.client = genai.Client(api_key=self.api_key)
            
            # Model configuration
            self.model_name = 'gemini-1.5-flash'
            
            self.enabled = True
            logger.info(f"Gemini evaluator initialized successfully with {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
            self.enabled = False
    
    def is_available(self) -> bool:
        """Check if Gemini evaluator is available and enabled"""
        return self.enabled and hasattr(self, 'client')
    
    def evaluate(
        self, 
        question: str, 
        student_answer: str, 
        model_answer: str, 
        subject_area: str = 'general',
        max_marks: int = 10
    ) -> Dict[str, Any]:
        """
        Evaluate student answer using Gemini LLM
        
        Args:
            question: The question text
            student_answer: Student's submitted answer
            model_answer: Expected/model answer
            subject_area: Subject area for context
            max_marks: Maximum marks for this question
            
        Returns:
            Dictionary with evaluation results
        """
        if not self.is_available():
            return self._fallback_response(max_marks, "Gemini evaluator not available")
        
        try:
            start_time = time.time()
            
            # Construct evaluation prompt
            prompt = self._build_evaluation_prompt(
                question, student_answer, model_answer, subject_area, max_marks
            )
            
            # Call Gemini API with new client
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
            # Parse response
            result = self._parse_response(response.text, max_marks)
            
            # Add metadata
            result['evaluation_time'] = time.time() - start_time
            result['evaluator'] = 'gemini'
            result['model_used'] = 'gemini-1.5-flash'
            
            logger.info(f"Gemini evaluation completed: {result['marks_awarded']}/{max_marks} in {result['evaluation_time']:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini evaluation failed: {str(e)}")
            return self._fallback_response(max_marks, str(e))
    
    def _build_evaluation_prompt(
        self, 
        question: str, 
        student_answer: str, 
        model_answer: str, 
        subject_area: str,
        max_marks: int
    ) -> str:
        """Build the evaluation prompt for Gemini"""
        
        prompt = f"""You are an expert educational evaluator grading {subject_area} examination answers.

**QUESTION:**
{question}

**MODEL/EXPECTED ANSWER:**
{model_answer}

**STUDENT'S ANSWER:**
{student_answer}

**GRADING CRITERIA:**
- Maximum Marks: {max_marks}
- Subject Area: {subject_area}
- Evaluate based on: correctness, completeness, understanding, clarity, and relevance

**INSTRUCTIONS:**
1. Carefully compare the student's answer with the model answer
2. Award marks based on:
   - Conceptual understanding (40%)
   - Accuracy of information (30%)
   - Completeness of coverage (20%)
   - Clarity and structure (10%)
3. Be fair but strict - partial credit for partially correct answers
4. Consider paraphrasing and different valid approaches
5. Deduct marks for incorrect information or irrelevant content

**REQUIRED OUTPUT FORMAT (JSON):**
{{
  "marks_awarded": <number between 0 and {max_marks}>,
  "percentage": <percentage score>,
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
  "missing_points": ["<missing point 1>", "<missing point 2>", ...],
  "feedback": "<detailed constructive feedback>",
  "detailed_scores": {{
    "conceptual_understanding": <score 0-100>,
    "accuracy": <score 0-100>,
    "completeness": <score 0-100>,
    "clarity": <score 0-100>
  }}
}}

Provide ONLY the JSON output, no additional text."""

        return prompt
    
    def _parse_response(self, response_text: str, max_marks: int) -> Dict[str, Any]:
        """Parse Gemini's response and extract evaluation data"""
        try:
            # Try to extract JSON from response
            # Sometimes LLMs wrap JSON in markdown code blocks
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            elif response_text.startswith('```'):
                response_text = response_text[3:]
            
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Extract and validate marks
            marks_awarded = min(max(int(data.get('marks_awarded', 0)), 0), max_marks)
            percentage = data.get('percentage', (marks_awarded / max_marks * 100))
            
            # Build result
            result = {
                'marks_awarded': marks_awarded,
                'similarity_score': percentage / 100,
                'feedback': data.get('feedback', 'No feedback provided'),
                'detailed_scores': data.get('detailed_scores', {}),
                'strengths': data.get('strengths', []),
                'weaknesses': data.get('weaknesses', []),
                'missing_points': data.get('missing_points', []),
                'max_marks': max_marks
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
            logger.debug(f"Response text: {response_text}")
            
            # Try to extract marks from text if JSON parsing fails
            return self._fallback_parse(response_text, max_marks)
        
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return self._fallback_response(max_marks, str(e))
    
    def _fallback_parse(self, response_text: str, max_marks: int) -> Dict[str, Any]:
        """Attempt to extract useful information even if JSON parsing fails"""
        import re
        
        # Try to find marks in text
        marks_match = re.search(r'marks[_\s]*awarded[:\s]*(\d+)', response_text, re.IGNORECASE)
        marks = int(marks_match.group(1)) if marks_match else max_marks // 2
        marks = min(max(marks, 0), max_marks)
        
        return {
            'marks_awarded': marks,
            'similarity_score': marks / max_marks,
            'feedback': response_text[:500],  # Use raw response as feedback
            'detailed_scores': {},
            'strengths': [],
            'weaknesses': [],
            'missing_points': [],
            'max_marks': max_marks,
            'parse_warning': 'JSON parsing failed, using fallback'
        }
    
    def _fallback_response(self, max_marks: int, error_msg: str) -> Dict[str, Any]:
        """Return fallback response when evaluation fails"""
        return {
            'marks_awarded': 0,
            'similarity_score': 0.0,
            'feedback': f"Gemini evaluation unavailable: {error_msg}",
            'detailed_scores': {},
            'strengths': [],
            'weaknesses': [],
            'missing_points': [],
            'max_marks': max_marks,
            'error': True
        }
