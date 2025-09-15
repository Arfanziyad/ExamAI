from typing import Dict, Any, List
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]

class OCRValidationService:
    def __init__(self):
        self.min_length = 50  # Minimum characters for meaningful text
        self.max_noise_ratio = 0.3  # Maximum ratio of noise characters
        self.min_words = 10  # Minimum number of words
        self.language = "en"  # Default language

    def validate_ocr_text(self, text: str, document_type: str = "general") -> ValidationResult:
        """
        Validate OCR extracted text for quality and completeness
        """
        if not text or not isinstance(text, str):
            return ValidationResult(
                is_valid=False,
                issues=["Empty or invalid text"],
                warnings=[],
                metrics={"length": 0, "words": 0, "noise_ratio": 1.0}
            )

        # Initialize lists for issues and warnings
        issues = []
        warnings = []
        metrics = {}

        # Basic text metrics
        text_length = len(text)
        words = self._get_words(text)
        word_count = len(words)
        avg_word_length = sum(len(w) for w in words) / max(word_count, 1)
        noise_ratio = self._calculate_noise_ratio(text)

        metrics.update({
            "length": text_length,
            "word_count": word_count,
            "avg_word_length": round(avg_word_length, 2),
            "noise_ratio": round(noise_ratio, 3)
        })

        # Validate text length
        if text_length < self.min_length:
            issues.append(f"Text is too short ({text_length} chars). Minimum required: {self.min_length}")

        # Validate word count
        if word_count < self.min_words:
            issues.append(f"Too few words ({word_count}). Minimum required: {self.min_words}")

        # Check for noise ratio
        if noise_ratio > self.max_noise_ratio:
            issues.append(f"High noise ratio ({noise_ratio:.2%}). Maximum allowed: {self.max_noise_ratio:.2%}")

        # Document type specific validations
        if document_type == "question":
            self._validate_question_paper(text, issues, warnings, metrics)
        elif document_type == "answer":
            self._validate_model_answer(text, issues, warnings, metrics)

        # Additional quality checks
        self._check_text_quality(text, issues, warnings, metrics)

        # Determine validity
        is_valid = len(issues) == 0

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            metrics=metrics
        )

    def _get_words(self, text: str) -> List[str]:
        """Extract meaningful words from text"""
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if len(w) > 1]  # Filter out single characters

    def _calculate_noise_ratio(self, text: str) -> float:
        """Calculate the ratio of noise characters to total characters"""
        if not text:
            return 1.0
        noise_chars = re.findall(r'[^a-zA-Z0-9\s.,!?()"\'-]', text)
        return len(noise_chars) / len(text)

    def _check_text_quality(self, text: str, issues: List[str], warnings: List[str], metrics: Dict[str, Any]):
        """Check general text quality indicators"""
        # Check for repetitive patterns
        repeated_words = self._find_repetitive_words(text)
        if repeated_words:
            warnings.append(f"Repetitive words detected: {', '.join(repeated_words[:3])}")

        # Check for common OCR errors
        ocr_errors = self._check_common_ocr_errors(text)
        if ocr_errors:
            warnings.append(f"Possible OCR errors detected: {', '.join(ocr_errors[:3])}")

        # Line analysis
        lines = text.split('\n')
        avg_line_length = sum(len(line.strip()) for line in lines) / max(len(lines), 1)
        metrics["avg_line_length"] = round(avg_line_length, 2)

        if avg_line_length < 20 and len(lines) > 5:
            warnings.append("Text appears fragmented with many short lines")

    def _validate_question_paper(self, text: str, issues: List[str], warnings: List[str], metrics: Dict[str, Any]):
        """Specific validations for question papers"""
        # Check for question markers
        question_markers = re.findall(r'(?i)(?:^|\n)\s*(?:q(?:uestion)?\.?\s*\d+|[\d]+\.)', text)
        metrics["question_count"] = len(question_markers)

        if not question_markers:
            warnings.append("No clear question markers detected")

        # Check for point/mark indicators
        mark_indicators = re.findall(r'(?i)(?:\d+\s*(?:marks?|points?)|\(\d+\))', text)
        if not mark_indicators:
            warnings.append("No mark allocations detected")

    def _validate_model_answer(self, text: str, issues: List[str], warnings: List[str], metrics: Dict[str, Any]):
        """Specific validations for model answers"""
        # Check for answer structure
        paragraphs = text.split('\n\n')
        metrics["paragraph_count"] = len(paragraphs)

        if len(paragraphs) < 2:
            warnings.append("Answer appears to lack proper structure/paragraphs")

        # Check for key terms
        key_terms = self._extract_key_terms(text)
        metrics["key_terms_count"] = len(key_terms)

        if len(key_terms) < 3:
            warnings.append("Few key terms detected in the answer")

    def _find_repetitive_words(self, text: str) -> List[str]:
        """Find unusually repetitive words"""
        words = self._get_words(text)
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Only check significant words
                word_counts[word] = word_counts.get(word, 0) + 1

        # Return words that appear more than 3 times
        return [word for word, count in word_counts.items() if count > 3]

    def _check_common_ocr_errors(self, text: str) -> List[str]:
        """Check for common OCR misrecognition patterns"""
        common_errors = []
        error_patterns = [
            (r'\bl\d+\b', 'number/letter confusion'),  # e.g., l0 instead of 10
            (r'[A-Za-z]{15,}', 'word run-together'),   # Very long "words"
            (r'(?:\d[A-Za-z]|[A-Za-z]\d){2,}', 'mixed characters')  # Mixed numbers/letters
        ]

        for pattern, error_type in error_patterns:
            if re.search(pattern, text):
                common_errors.append(error_type)

        return common_errors

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract potentially important terms"""
        # Simple key term extraction based on capitalization and special markers
        key_terms = re.findall(r'(?:[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)*|\*\*.*?\*\*|__.*?__)', text)
        return list(set(key_terms))  # Remove duplicates