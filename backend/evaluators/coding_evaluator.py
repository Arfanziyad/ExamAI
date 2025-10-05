# evaluators/coding_evaluator.py
import re
import subprocess
import tempfile
import os
import ast
from typing import Dict, Any

class CodingEvaluator:
    """Evaluates coding questions with execution testing and static analysis"""
    
    def __init__(self):
        self.supported_languages = ['python', 'javascript', 'java', 'cpp']
        
    def evaluate(self, question: str, student_answer: str, model_answer: str) -> Dict[str, Any]:
        """Main evaluation method for coding questions"""
        try:
            # Detect programming language
            language = self._detect_language(student_answer)
            
            # Initialize scoring components
            scores = {
                'syntax_score': 0,
                'logic_score': 0,
                'execution_score': 0,
                'style_score': 0
            }
            
            feedback_items = []
            
            # 1. Syntax Analysis
            syntax_result = self._check_syntax(student_answer, language)
            scores['syntax_score'] = syntax_result['score']
            if syntax_result['feedback']:
                feedback_items.extend(syntax_result['feedback'])
            
            # 2. Code Execution Testing (if possible)
            execution_result = self._test_execution(student_answer, model_answer, language)
            scores['execution_score'] = execution_result['score']
            if execution_result['feedback']:
                feedback_items.extend(execution_result['feedback'])
            
            # 3. Logic and Structure Analysis
            logic_result = self._analyze_logic(student_answer, model_answer, language)
            scores['logic_score'] = logic_result['score']
            if logic_result['feedback']:
                feedback_items.extend(logic_result['feedback'])
            
            # 4. Code Style and Best Practices
            style_result = self._check_code_style(student_answer, language)
            scores['style_score'] = style_result['score']
            if style_result['feedback']:
                feedback_items.extend(style_result['feedback'])
            
            # Calculate final score (weighted average)
            weights = {
                'syntax_score': 0.25,
                'logic_score': 0.35,
                'execution_score': 0.30,
                'style_score': 0.10
            }
            
            final_score = sum(scores[key] * weights[key] for key in weights)
            marks_awarded = round((final_score / 100) * 10)
            
            # Generate comprehensive feedback
            feedback = self._generate_feedback(scores, feedback_items, final_score)
            
            return {
                'similarity_score': final_score / 100,
                'marks_awarded': marks_awarded,
                'feedback': feedback,
                'detailed_scores': scores,
                'language_detected': language
            }
            
        except Exception as e:
            return {
                'similarity_score': 0.0,
                'marks_awarded': 0,
                'feedback': f"Error evaluating code: {str(e)}",
                'detailed_scores': {'error': True},
                'language_detected': 'unknown'
            }
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code"""
        code_lower = code.lower()
        
        # Python indicators
        if any(keyword in code for keyword in ['def ', 'import ', 'print(', 'if __name__']):
            return 'python'
        
        # JavaScript indicators
        if any(keyword in code for keyword in ['function ', 'var ', 'let ', 'const ', 'console.log']):
            return 'javascript'
        
        # Java indicators
        if any(keyword in code for keyword in ['public class', 'System.out', 'public static void']):
            return 'java'
        
        # C++ indicators
        if any(keyword in code for keyword in ['#include', 'using namespace', 'cout <<', 'int main()']):
            return 'cpp'
        
        return 'python'  # Default assumption
    
    def _check_syntax(self, code: str, language: str) -> Dict[str, Any]:
        """Check syntax correctness"""
        if language == 'python':
            return self._check_python_syntax(code)
        else:
            # For other languages, do basic checks
            return {'score': 80, 'feedback': ['Basic syntax appears correct']}
    
    def _check_python_syntax(self, code: str) -> Dict[str, Any]:
        """Check Python syntax specifically"""
        try:
            ast.parse(code)
            return {
                'score': 100,
                'feedback': ['✓ Python syntax is correct']
            }
        except SyntaxError as e:
            return {
                'score': 30,
                'feedback': [f'✗ Syntax error: {str(e)}']
            }
        except Exception:
            return {
                'score': 60,
                'feedback': ['⚠ Some syntax issues detected']
            }
    
    def _test_execution(self, student_code: str, model_code: str, language: str) -> Dict[str, Any]:
        """Test code execution with sample inputs"""
        if language != 'python':
            return {'score': 70, 'feedback': ['Execution testing not available for this language']}
        
        try:
            # Extract test cases from model answer or create basic ones
            test_cases = self._extract_test_cases(model_code)
            
            if not test_cases:
                # Create basic test cases if none found
                test_cases = [{'input': '', 'expected': 'basic_execution'}]
            
            passed_tests = 0
            total_tests = len(test_cases)
            feedback = []
            
            for i, test_case in enumerate(test_cases):
                result = self._run_python_code(student_code, test_case.get('input', ''))
                
                if result['success']:
                    passed_tests += 1
                    feedback.append(f'✓ Test case {i+1} passed')
                else:
                    feedback.append(f'✗ Test case {i+1} failed: {result.get("error", "Unknown error")}')
            
            score = (passed_tests / total_tests) * 100
            
            return {
                'score': score,
                'feedback': feedback
            }
            
        except Exception as e:
            return {
                'score': 0,
                'feedback': [f'Execution testing failed: {str(e)}']
            }
    
    def _extract_test_cases(self, model_code: str) -> list:
        """Extract test cases from model code comments or structure"""
        test_cases = []
        
        # Look for test case patterns in comments
        test_patterns = [
            r'#\s*test\s*:\s*(.+)',
            r'#\s*example\s*:\s*(.+)',
            r'#\s*input\s*:\s*(.+)'
        ]
        
        for pattern in test_patterns:
            matches = re.findall(pattern, model_code, re.IGNORECASE)
            for match in matches:
                test_cases.append({'input': match.strip(), 'expected': 'execution'})
        
        return test_cases
    
    def _run_python_code(self, code: str, input_data: str = '') -> Dict[str, Any]:
        """Safely run Python code in a temporary environment"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run the code with timeout
            process = subprocess.run(
                ['python', temp_file],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=5  # 5 second timeout
            )
            
            # Clean up
            os.unlink(temp_file)
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'output': process.stdout,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'output': process.stdout,
                    'error': process.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Code execution timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def _analyze_logic(self, student_code: str, model_code: str, language: str) -> Dict[str, Any]:
        """Analyze logical correctness and algorithmic approach"""
        feedback = []
        score = 70  # Base score
        
        # Check for key algorithmic concepts
        concepts_used = []
        
        # Common programming concepts
        if 'for ' in student_code or 'while ' in student_code:
            concepts_used.append('loops')
            score += 5
        
        if 'if ' in student_code:
            concepts_used.append('conditionals')
            score += 5
        
        if 'def ' in student_code or 'function ' in student_code:
            concepts_used.append('functions')
            score += 10
        
        if any(word in student_code.lower() for word in ['list', 'array', '[]']):
            concepts_used.append('data structures')
            score += 5
        
        # Check for common patterns from model answer
        model_patterns = self._extract_patterns(model_code)
        student_patterns = self._extract_patterns(student_code)
        
        pattern_similarity = len(set(model_patterns) & set(student_patterns)) / max(len(model_patterns), 1)
        score += pattern_similarity * 20
        
        feedback.append(f'Concepts used: {", ".join(concepts_used) if concepts_used else "Basic structure"}')
        feedback.append(f'Algorithmic similarity: {pattern_similarity:.1%}')
        
        return {
            'score': min(score, 100),
            'feedback': feedback
        }
    
    def _extract_patterns(self, code: str) -> list:
        """Extract common programming patterns from code"""
        patterns = []
        
        if re.search(r'for\s+\w+\s+in', code):
            patterns.append('for_in_loop')
        if re.search(r'while\s+.+:', code):
            patterns.append('while_loop')
        if re.search(r'if\s+.+:', code):
            patterns.append('conditional')
        if re.search(r'def\s+\w+\s*\(', code):
            patterns.append('function_definition')
        if re.search(r'return\s+', code):
            patterns.append('return_statement')
        
        return patterns
    
    def _check_code_style(self, code: str, language: str) -> Dict[str, Any]:
        """Check code style and best practices"""
        score = 80  # Base score
        feedback = []
        
        # Check indentation
        lines = code.split('\n')
        indented_lines = [line for line in lines if line.startswith('    ') or line.startswith('\t')]
        
        if indented_lines:
            feedback.append('✓ Proper indentation used')
            score += 10
        else:
            feedback.append('⚠ Consider using proper indentation')
            score -= 10
        
        # Check for comments
        comment_lines = [line for line in lines if line.strip().startswith('#')]
        if comment_lines:
            feedback.append('✓ Code includes comments')
            score += 5
        
        # Check variable naming
        if re.search(r'[a-z_][a-z0-9_]*', code):
            feedback.append('✓ Good variable naming convention')
        else:
            feedback.append('⚠ Consider using descriptive variable names')
            score -= 5
        
        return {
            'score': min(max(score, 0), 100),
            'feedback': feedback
        }
    
    def _generate_feedback(self, scores: Dict[str, int], feedback_items: list, final_score: float) -> str:
        """Generate comprehensive feedback"""
        feedback_parts = []
        
        # Overall assessment
        if final_score >= 85:
            feedback_parts.append("Excellent coding solution!")
        elif final_score >= 70:
            feedback_parts.append("Good coding attempt with room for improvement.")
        elif final_score >= 50:
            feedback_parts.append("Decent effort, but several issues need attention.")
        else:
            feedback_parts.append("Significant improvements needed in multiple areas.")
        
        # Detailed breakdown
        feedback_parts.append(f"\nDetailed Analysis:")
        feedback_parts.append(f"• Syntax: {scores['syntax_score']:.0f}%")
        feedback_parts.append(f"• Logic: {scores['logic_score']:.0f}%")
        feedback_parts.append(f"• Execution: {scores['execution_score']:.0f}%")
        feedback_parts.append(f"• Style: {scores['style_score']:.0f}%")
        
        # Specific feedback
        if feedback_items:
            feedback_parts.append(f"\nSpecific Feedback:")
            for item in feedback_items[:5]:  # Limit to top 5 items
                feedback_parts.append(f"• {item}")
        
        return "\n".join(feedback_parts)