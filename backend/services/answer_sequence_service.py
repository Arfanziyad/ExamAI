"""
Answer Sequence Analyzer - Handles flexible answer ordering
Detects and parses student answers regardless of the order they were written
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AnswerSection:
    """Represents a detected answer section"""
    question_number: str
    sub_question: Optional[str]
    content: str
    position_in_text: int
    confidence: float

class AnswerSequenceAnalyzer:
    """Analyzes and extracts answer sequences from student submissions"""
    
    def __init__(self):
        # Pattern for detecting question numbers and sub-questions
        self.question_patterns = [
            r'(?:^|\n)\s*(?:question\s*)?(\d+)\s*[.)]\s*([a-z]?)\s*[.)]?\s*(.*?)(?=(?:\n\s*(?:question\s*)?\d+\s*[.)])|$)',
            r'(?:^|\n)\s*(\d+)\s*([a-z])\s*[.)]\s*(.*?)(?=(?:\n\s*\d+\s*[a-z]\s*[.)])|(?:\n\s*\d+\s*[.)])|$)',
            r'(?:^|\n)\s*(\d+)\s*[.)]\s*(.*?)(?=(?:\n\s*\d+\s*[.)])|$)',
            r'(?:^|\n)\s*([a-z])\s*[.)]\s*(.*?)(?=(?:\n\s*[a-z]\s*[.)])|$)'
        ]
        
        # Common answer section indicators
        self.section_indicators = [
            'answer', 'solution', 'ans', 'sol', 'given', 'to find', 'required'
        ]
    
    def analyze_submission(self, extracted_text: str, expected_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze student submission and extract answer sections in any order
        
        Args:
            extracted_text: OCR extracted text from student's answer sheet
            expected_questions: List of expected questions with their details
            
        Returns:
            Dictionary containing:
            - answer_sections: List of detected answer sections
            - answer_sequence: Detected order of answers
            - sequence_confidence: Overall confidence in detection
            - parsed_answers: Mapped answers to questions
        """
        try:
            # Clean and normalize the text
            normalized_text = self._normalize_text(extracted_text)
            
            # Detect answer sections
            sections = self._detect_answer_sections(normalized_text)
            
            # Map sections to expected questions
            mapped_answers = self._map_sections_to_questions(sections, expected_questions)
            
            # Determine answer sequence
            sequence = self._determine_sequence(sections)
            
            # Calculate confidence
            confidence = self._calculate_confidence(sections, expected_questions)
            
            result = {
                'answer_sections': [self._section_to_dict(section) for section in sections],
                'answer_sequence': sequence,
                'sequence_confidence': confidence,
                'parsed_answers': mapped_answers,
                'analysis_metadata': {
                    'total_sections_found': len(sections),
                    'expected_questions': len(expected_questions),
                    'matching_rate': len(mapped_answers) / max(len(expected_questions), 1),
                    'text_length': len(normalized_text)
                }
            }
            
            logger.info(f"Answer sequence analysis completed: {len(sections)} sections found, confidence: {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Answer sequence analysis failed: {str(e)}")
            return self._fallback_analysis(extracted_text, expected_questions)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better pattern matching"""
        # Normalize line endings first so we can preserve line boundaries
        text = re.sub(r'\r\n|\r', '\n', text)
        # Replace page breaks and form feeds with newlines
        text = re.sub(r'[\f\x0c]', '\n', text)
        # Collapse multiple spaces/tabs but preserve newlines
        text = re.sub(r'[ \t]+', ' ', text)
        # Collapse multiple blank lines to a maximum of two
        text = re.sub(r'\n{2,}', '\n\n', text)
        return text.strip()
    
    def _detect_answer_sections(self, text: str) -> List[AnswerSection]:
        """Detect answer sections using various patterns"""
        sections = []
        
        for pattern in self.question_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                groups = match.groups()
                if not groups:  # Handle empty tuple case
                    continue
                    
                question_num = groups[0] if len(groups) > 0 and groups[0] else ""
                sub_question = groups[1] if len(groups) > 1 and groups[1] else None
                content = groups[-1] if len(groups) > 0 and groups[-1] else ""
                
                if content.strip():  # Only include sections with actual content
                    section = AnswerSection(
                        question_number=question_num,
                        sub_question=sub_question,
                        content=content.strip(),
                        position_in_text=match.start(),
                        confidence=self._calculate_section_confidence(match, text)
                    )
                    sections.append(section)
        
        # Remove duplicate sections (same position, similar content)
        sections = self._deduplicate_sections(sections)
        
        # Sort by position in text
        sections.sort(key=lambda x: x.position_in_text)
        
        return sections
    
    def _map_sections_to_questions(self, sections: List[AnswerSection], expected_questions: List[Dict[str, Any]]) -> Dict[str, str]:
        """Map detected sections to expected questions"""
        mapped = {}
        
        for section in sections:
            # Try to find matching expected question
            question_key = self._find_matching_question(section, expected_questions)
            
            if question_key:
                # Combine sub-questions if they belong to the same main question
                if question_key in mapped:
                    mapped[question_key] += f"\n\n{section.sub_question or 'continued'}: {section.content}"
                else:
                    mapped[question_key] = section.content
        
        return mapped
    
    def _find_matching_question(self, section: AnswerSection, expected_questions: List[Dict[str, Any]]) -> Optional[str]:
        """Find which expected question this section answers"""
        
        # Try exact question number match first
        for question in expected_questions:
            question_num = str(question.get('question_number', ''))
            if section.question_number == question_num:
                if section.sub_question:
                    return f"{question_num}_{section.sub_question}"
                else:
                    return question_num
        
        # Try content-based matching if no direct number match
        for question in expected_questions:
            question_text = question.get('question_text', '').lower()
            section_content = section.content.lower()
            
            # Look for key terms from question in the answer
            question_keywords = self._extract_keywords(question_text)
            if self._has_keyword_overlap(section_content, question_keywords):
                question_num = str(question.get('question_number', ''))
                return f"{question_num}_content_match"
        
        return None
    
    def _calculate_section_confidence(self, match: re.Match, full_text: str) -> float:
        """Calculate confidence score for a detected section"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for clear question patterns
        if re.search(r'\d+\s*[.)]\s*[a-z]\s*[.)]', match.group()):
            confidence += 0.3
        elif re.search(r'\d+\s*[.)]', match.group()):
            confidence += 0.2
        
        # Boost confidence if content is substantial
        content_length = len(match.groups()[-1].strip())
        if content_length > 50:
            confidence += 0.2
        elif content_length > 20:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _determine_sequence(self, sections: List[AnswerSection]) -> List[str]:
        """Determine the actual sequence in which questions were answered"""
        sequence = []
        
        for section in sections:
            if section.sub_question:
                sequence.append(f"{section.question_number}{section.sub_question}")
            else:
                sequence.append(section.question_number)
        
        return sequence
    
    def _calculate_confidence(self, sections: List[AnswerSection], expected_questions: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in the analysis"""
        if not sections:
            return 0.0
        
        # Average section confidence
        avg_section_confidence = sum(s.confidence for s in sections) / len(sections)
        
        # Coverage score (how many expected questions we found)
        coverage_score = min(len(sections) / len(expected_questions), 1.0) if expected_questions else 0.5
        
        # Pattern consistency score
        pattern_score = self._calculate_pattern_consistency(sections)
        
        return (avg_section_confidence * 0.4 + coverage_score * 0.4 + pattern_score * 0.2)
    
    def _calculate_pattern_consistency(self, sections: List[AnswerSection]) -> float:
        """Check if detected patterns are consistent"""
        if len(sections) <= 1:
            return 1.0
        
        # Check if question numbers are reasonable
        question_numbers = [s.question_number for s in sections if s.question_number.isdigit()]
        if question_numbers:
            numbers = [int(q) for q in question_numbers]
            # Should be within reasonable range (1-20 typically)
            if all(1 <= num <= 20 for num in numbers):
                return 0.8
            else:
                return 0.4
        
        return 0.6
    
    def _deduplicate_sections(self, sections: List[AnswerSection]) -> List[AnswerSection]:
        """Remove duplicate or overlapping sections"""
        if not sections:
            return sections
        
        # Sort by position
        sections.sort(key=lambda x: x.position_in_text)
        
        deduplicated = [sections[0]]
        
        for current in sections[1:]:
            last_added = deduplicated[-1]
            
            # Check if this section overlaps significantly with the last one
            if abs(current.position_in_text - last_added.position_in_text) > 50:
                # Check content similarity
                if not self._is_content_similar(current.content, last_added.content):
                    deduplicated.append(current)
        
        return deduplicated
    
    def _is_content_similar(self, content1: str, content2: str, threshold: float = 0.7) -> bool:
        """Check if two content strings are similar (simple word overlap check)"""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1.intersection(words2))
        total_unique = len(words1.union(words2))
        
        similarity = overlap / total_unique if total_unique > 0 else 0
        return similarity >= threshold
    
    def _extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """Extract meaningful keywords from text"""
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common words and keep only meaningful terms
        stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        keywords = [word for word in words if len(word) >= min_length and word not in stopwords]
        return keywords[:10]  # Top 10 keywords
    
    def _has_keyword_overlap(self, text: str, keywords: List[str], threshold: int = 2) -> bool:
        """Check if text contains enough keywords"""
        text_lower = text.lower()
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        return matches >= threshold
    
    def _section_to_dict(self, section: AnswerSection) -> Dict[str, Any]:
        """Convert AnswerSection to dictionary"""
        return {
            'question_number': section.question_number,
            'sub_question': section.sub_question,
            'content': section.content,
            'position_in_text': section.position_in_text,
            'confidence': section.confidence
        }
    
    def _fallback_analysis(self, text: str, expected_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback analysis when primary method fails"""
        return {
            'answer_sections': [{
                'question_number': '1',
                'sub_question': None,
                'content': text,
                'position_in_text': 0,
                'confidence': 0.1
            }],
            'answer_sequence': ['1'],
            'sequence_confidence': 0.1,
            'parsed_answers': {'1': text},
            'analysis_metadata': {
                'total_sections_found': 1,
                'expected_questions': len(expected_questions),
                'matching_rate': 1.0 / max(len(expected_questions), 1),
                'text_length': len(text),
                'fallback_used': True
            }
        }

def analyze_answer_sequence(extracted_text: str, expected_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main function to analyze answer sequence from extracted text
    
    Args:
        extracted_text: OCR extracted text from student submission
        expected_questions: List of expected question details
        
    Returns:
        Analysis results including detected sequence and parsed answers
    """
    analyzer = AnswerSequenceAnalyzer()
    return analyzer.analyze_submission(extracted_text, expected_questions)