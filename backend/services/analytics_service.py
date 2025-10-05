from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List, Optional, cast, Union
from collections import Counter, defaultdict
import statistics

def safe_convert(value: Any) -> float:
    """Safely convert a SQLAlchemy value to float"""
    try:
        if hasattr(value, 'scalar'):
            return float(str(value.scalar()))
        return float(str(value))
    except (ValueError, TypeError, AttributeError):
        return 0.0
from models import Submission, Evaluation, Question, QuestionPaper

class AnalyticsService:
    
    @staticmethod
    def get_performance_analytics(db: Session, question_paper_id: Optional[int] = None) -> Dict[str, Any]:
        """Get overall performance analytics"""
        
        # Base query
        query = db.query(Evaluation).join(Submission).join(Question)
        
        if question_paper_id:
            query = query.filter(Question.question_paper_id == question_paper_id)
        
        evaluations = query.all()
        
        if not evaluations:
            return {
                'total_submissions': 0,
                'average_score': 0,
                'score_distribution': {},
                'grade_distribution': {},
                'subject_performance': {},
                'improvement_areas': []
            }
        
        # Calculate statistics
        # Extract values from SQLAlchemy objects
        scores = []
        percentages = []
        for eval in evaluations:
            marks = safe_convert(eval.marks_awarded)
            max_marks = safe_convert(eval.max_marks)
            if max_marks > 0:
                scores.append(marks)
                percentages.append((marks / max_marks) * 100)
        
        # Score distribution by ranges
        score_ranges = {
            'Excellent (90-100%)': 0,
            'Very Good (80-89%)': 0,
            'Good (70-79%)': 0,
            'Satisfactory (60-69%)': 0,
            'Needs Improvement (50-59%)': 0,
            'Poor (<50%)': 0
        }
        
        for percentage in percentages:
            percentage_val = float(percentage)
            if percentage_val >= 90:
                score_ranges['Excellent (90-100%)'] += 1
            elif percentage_val >= 80:
                score_ranges['Very Good (80-89%)'] += 1
            elif percentage_val >= 70:
                score_ranges['Good (70-79%)'] += 1
            elif percentage_val >= 60:
                score_ranges['Satisfactory (60-69%)'] += 1
            elif percentage_val >= 50:
                score_ranges['Needs Improvement (50-59%)'] += 1
            else:
                score_ranges['Poor (<50%)'] += 1
        
        # Subject-wise performance
        subject_performance = defaultdict(list)
        for eval in evaluations:
            subject = eval.submission.question.subject_area
            percentage = (eval.marks_awarded / eval.max_marks) * 100
            subject_performance[subject].append(percentage)
        
        subject_stats = {}
        for subject, scores in subject_performance.items():
            subject_stats[subject] = {
                'average': round(statistics.mean(scores), 2),
                'count': len(scores),
                'median': round(statistics.median(scores), 2)
            }
        
        # Common improvement areas (from detailed scores)
        improvement_areas = []
        semantic_scores = []
        keyword_scores = []
        structure_scores = []
        comprehensiveness_scores = []
        
        for eval in evaluations:
            detailed_scores = getattr(eval, 'detailed_scores', None)
            if detailed_scores:
                semantic_scores.append(eval.detailed_scores.get('semantic', 0))
                keyword_scores.append(eval.detailed_scores.get('keyword', 0))
                structure_scores.append(eval.detailed_scores.get('structure', 0))
                comprehensiveness_scores.append(eval.detailed_scores.get('comprehensiveness', 0))
        
        if semantic_scores:
            avg_semantic = statistics.mean(semantic_scores)
            avg_keyword = statistics.mean(keyword_scores)
            avg_structure = statistics.mean(structure_scores)
            avg_comprehensiveness = statistics.mean(comprehensiveness_scores)
            
            areas = [
                ('Content Understanding', avg_semantic),
                ('Key Terms Usage', avg_keyword),
                ('Answer Structure', avg_structure),
                ('Completeness', avg_comprehensiveness)
            ]
            
            # Sort by lowest scores first (areas needing most improvement)
            areas.sort(key=lambda x: x[1])
            improvement_areas = [{'area': area[0], 'score': round(area[1], 1)} for area in areas]
        
        return {
            'total_submissions': len(evaluations),
            'average_score': round(statistics.mean(percentages), 2) if percentages else 0,
            'median_score': round(statistics.median(percentages), 2) if percentages else 0,
            'score_distribution': score_ranges,
            'subject_performance': subject_stats,
            'improvement_areas': improvement_areas
        }
    
    @staticmethod
    def get_student_performance(db: Session, student_name: str) -> Dict[str, Any]:
        """Get performance analytics for a specific student"""
        
        submissions = db.query(Submission).filter(
            Submission.student_name.ilike(f"%{student_name}%")
        ).all()
        
        if not submissions:
            return {
                'student_name': student_name,
                'total_submissions': 0,
                'average_score': 0,
                'submissions_history': [],
                'improvement_trend': [],
                'strengths': [],
                'areas_for_improvement': []
            }
        
        # Get submissions with evaluations
        submissions_with_eval = []
        scores_over_time = []
        
        for submission in submissions:
            # Get the first evaluation (since we changed to one-to-many relationship)
            evaluation = submission.evaluations[0] if submission.evaluations else None
            if evaluation:
                eval_data = evaluation
                percentage = (eval_data.marks_awarded / eval_data.max_marks) * 100
                
                submission_data = {
                    'id': submission.id,
                    'question_text': submission.question.question_text[:100] + "...",
                    'subject': submission.question.subject_area,
                    'score': eval_data.marks_awarded,
                    'max_score': eval_data.max_marks,
                    'percentage': round(percentage, 1),
                    'submitted_at': submission.submitted_at,
                    'detailed_scores': eval_data.detailed_scores
                }
                
                submissions_with_eval.append(submission_data)
                scores_over_time.append(percentage)
        
        # Calculate improvement trend
        improvement_trend = []
        if len(scores_over_time) > 1:
            for i in range(1, len(scores_over_time)):
                change = scores_over_time[i] - scores_over_time[i-1]
                improvement_trend.append({
                    'submission_number': i + 1,
                    'score': scores_over_time[i],
                    'change': round(change, 1)
                })
        
        # Analyze strengths and weaknesses
        all_detailed_scores = [s['detailed_scores'] for s in submissions_with_eval if s['detailed_scores']]
        
        strengths = []
        areas_for_improvement = []
        
        if all_detailed_scores:
            avg_scores = {
                'semantic': statistics.mean([s.get('semantic', 0) for s in all_detailed_scores]),
                'keyword': statistics.mean([s.get('keyword', 0) for s in all_detailed_scores]),
                'structure': statistics.mean([s.get('structure', 0) for s in all_detailed_scores]),
                'comprehensiveness': statistics.mean([s.get('comprehensiveness', 0) for s in all_detailed_scores])
            }
            
            sorted_areas = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Top 2 are strengths, bottom 2 need improvement
            strengths = [{'area': area.replace('_', ' ').title(), 'score': round(score, 1)} 
                        for area, score in sorted_areas[:2]]
            areas_for_improvement = [{'area': area.replace('_', ' ').title(), 'score': round(score, 1)} 
                                   for area, score in sorted_areas[-2:]]
        
        average_score = round(statistics.mean(scores_over_time), 2) if scores_over_time else 0
        
        return {
            'student_name': student_name,
            'total_submissions': len(submissions_with_eval),
            'average_score': average_score,
            'submissions_history': sorted(submissions_with_eval, key=lambda x: x['submitted_at'], reverse=True),
            'improvement_trend': improvement_trend,
            'strengths': strengths,
            'areas_for_improvement': areas_for_improvement
        }
    
    @staticmethod
    def get_question_analytics(db: Session, question_id: int) -> Dict[str, Any]:
        """Get analytics for a specific question"""
        
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return {'error': 'Question not found'}
        
        evaluations = db.query(Evaluation).join(Submission).filter(
            Submission.question_id == question_id
        ).all()
        
        if not evaluations:
            return {
                'question_id': question_id,
                'question_text': question.question_text,
                'total_attempts': 0,
                'average_score': 0,
                'difficulty_level': 'No data',
                'common_mistakes': [],
                'top_answers': []
            }
        
        scores = [eval.marks_awarded for eval in evaluations]
        percentages = [(eval.marks_awarded / eval.max_marks) * 100 for eval in evaluations]
        # Convert percentages to float values for mean calculation
        float_percentages = [safe_convert(p) for p in percentages]
        average_percentage = statistics.mean(float_percentages)
        
        # Determine difficulty level
        if average_percentage >= 80:
            difficulty = 'Easy'
        elif average_percentage >= 60:
            difficulty = 'Medium'
        else:
            difficulty = 'Hard'
        
        # Find common issues from detailed scores
        common_mistakes = []
        detailed_scores = getattr(evaluations[0], 'detailed_scores', None)
        if detailed_scores:
            semantic_scores = [getattr(eval, 'detailed_scores', {}).get('semantic', 0) for eval in evaluations]
            keyword_scores = [getattr(eval, 'detailed_scores', {}).get('keyword', 0) for eval in evaluations]
            structure_scores = [getattr(eval, 'detailed_scores', {}).get('structure', 0) for eval in evaluations]
            comprehensiveness_scores = [getattr(eval, 'detailed_scores', {}).get('comprehensiveness', 0) for eval in evaluations]
            
            if statistics.mean(semantic_scores) < 60:
                common_mistakes.append('Poor conceptual understanding')
            if statistics.mean(keyword_scores) < 60:
                common_mistakes.append('Missing key terminology')
            if statistics.mean(structure_scores) < 60:
                common_mistakes.append('Weak answer structure')
            if statistics.mean(comprehensiveness_scores) < 60:
                common_mistakes.append('Incomplete coverage of topic')
        
        return {
            'question_id': question_id,
            'question_text': question.question_text,
            'subject_area': question.subject_area,
            'max_marks': question.max_marks,
            'total_attempts': len(evaluations),
            'average_score': round(average_percentage, 2),
            'difficulty_level': difficulty,
            'score_distribution': {
                'excellent': sum(1 for p in percentages if safe_convert(p) >= 90),
                'good': sum(1 for p in percentages if 70 <= safe_convert(p) < 90),
                'average': sum(1 for p in percentages if 50 <= safe_convert(p) < 70),
                'poor': sum(1 for p in percentages if safe_convert(p) < 50)
            },
            'common_mistakes': common_mistakes
        }   