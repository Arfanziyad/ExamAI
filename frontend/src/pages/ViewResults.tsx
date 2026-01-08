import { useState, useEffect } from 'react';
import { CheckCircle, ChevronDown, ChevronUp, Clock, User, Award, Filter } from 'lucide-react';
import Loading from '../components/Loading';
import { getAllEvaluationResults, getTests } from '../services/api';

// Define types for submission and evaluation data
interface EvaluationData {
  id: number;
  similarity_score: number;
  marks_awarded: number;
  max_marks: number;
  detailed_scores: Record<string, number>;
  ai_feedback: string;
  evaluation_time: string;
  created_at: string;
}

interface SubmissionData {
  id: number;
  question_id: number;
  question_paper_id: number;
  student_name: string;
  handwriting_image_path: string;
  extracted_text?: string;
  ocr_confidence?: number;
  submitted_at: string;
  evaluation?: EvaluationData;
}

// Grouped submission by student
interface StudentResult {
  student_name: string;
  submissions: SubmissionData[];
  total_marks: number;
  max_marks: number;
  percentage: number;
}

// QuestiallSubmissions, setAllSubmissions] = useState<SubmissionData[]>([]);
  const [studentResults, setStudentResults] = useState<StudentResult[]>([]);
  const [questionPapers, setQuestionPapers] = useState<QuestionPaper[]>([]);
  const [selectedPaperId, setSelectedPaperId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedStudent, setExpandedStudent] = useState<string | null>(null);

  // Fetch question papers and submissions on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [submissionsData, papersData] = await Promise.all([
          getAllEvaluationResults(),
          getTests()
        ]);
        
        // Filter out submissions without evaluations
        const evaluatedSubmissions = submissionsData.filter((submission: SubmissionData) => submission.evaluation);
        setAllSubmissions(evaluatedSubmissions);
        setQuestionPapers(papersData);
        
        // Auto-select first question paper if available
        if (papersData.length > 0) {
          setSelectedPaperId(papersData[0].id);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
        setAllSubmissions([]);
        setQuestionPapers([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Filter and group submissions when selected paper changes
  useEffect(() => {
    if (!selectedPaperId) {
      setStudentResults([]);
      return;
    }

    // Filter submissions for selected question paper
    const filteredSubmissions = allSubmissions.filter(
      sub => sub.question_paper_id === selectedPaperId
    );

    // Group by student name
    const grouped = filteredSubmissions.reduce((acc, submission) => {
      const studentName = submission.student_name;
      if (!acc[studentName]) {
        acc[studentName] = [];
      }
      acc[studentName].push(submission);
      return acc;
    }, {} as Record<string, SubmissionData[]>);

    // Convert to array and calculate totals
    const results: StudentResult[] = Object.entries(grouped).map(([studentName, submissions]) => {
      const total_marks = submissions.reduce((sum, sub) => sum + (sub.evaluation?.marks_awarded || 0), 0);
      const max_marks = submissions.reduce((sum, sub) => sum + (sub.evaluation?.max_marks || 0), 0);
      const percentage = max_marks > 0 ? Math.round((total_marks / max_marks) * 100) : 0;

      return {
        student_name: studentName,
        submissions: submissions.sort((a, b) => a.question_id - b.question_id),
        total_marks,
        max_marks,
        percentage
      };
    });

    // Sort by student name
    results.sort((a, b) => a.student_name.localeCompare(b.student_name));
    setStudentResults(results);
  }, [selectedPaperId, allSubmissions  results.sort((a, b) => a.student_name.localeCompare(b.student_name));
        setStudentResults(results);
      } catch (error) {
        console.error('Error fetching results:', error);
        setStudentResults([]);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, []);

  const toggleStudent = (studentName: string) => {
    setExpandedStudent(expandedStudent === studentName ? null : studentName);
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Evaluation Results</h1>
        <p className="text-gray-600">View detailed student performance with answers and marks</p>
        
        {/* Test Selector */}
        {questionPapers.length > 0 && (
          <div className="mt-4 flex items-center space-x-3">
            <Filter className="h-5 w-5 text-gray-500" />
            <label htmlFor="test-select" className="text-sm font-medium text-gray-700">
              Select Test:
            </label>
            <select
              id="test-select"
              value={selectedPaperId || ''}
              onChange={(e) => setSelectedPaperId(Number(e.target.value))}
              className="flex-1 max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white text-gray-900"
            >
              {questionPapers.map((paper) => (
                <option key={paper.id} value={paper.id}>
                  {paper.title} - {paper.subject} {paper.created_at && `(${new Date(paper.created_at).toLocaleDateString()})`}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Results */}
      {studentResults.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            {selectedPaperId 
              ? 'No evaluation results available for this test yet.' 
              : 'No tests available yet.'}
          </p>
          <p className="text-sm text-gray-400 mt-1">
            {selectedPaperId 
              ? 'Submit some answers to see evaluation results here.' 
              : 'Create a test first to see results.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {studentResults.map((studentResult) => (
            <div 
              key={studentResult.student_name} 
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            >
              {/* Student Header - Clickable */}
              <button
                onClick={() => toggleStudent(studentResult.student_name)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className="bg-indigo-100 p-3 rounded-lg">
                    <User className="h-6 w-6 text-indigo-600" />
                  </div>
                  <div className="text-left">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {studentResult.student_name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {studentResult.submissions.length} question{studentResult.submissions.length !== 1 ? 's' : ''} answered
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-6">
                  {/* Overall Score */}
                  <div className="text-right">
                    <div className="flex items-center space-x-2">
                      <Award className="h-5 w-5 text-yellow-500" />
                      <span className={`text-2xl font-bold ${
                        studentResult.percentage >= 80 ? 'text-green-600' :
                        studentResult.percentage >= 60 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {studentResult.percentage}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {studentResult.total_marks} / {studentResult.max_marks} marks
                    </p>
                  </div>

                  {/* Expand/Collapse Icon */}
                  {expandedStudent === studentResult.student_name ? (
                    <ChevronUp className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-400" />
                  )}
                </div>
              </button>

              {/* Expanded Details */}
              {expandedStudent === studentResult.student_name && (
                <div className="border-t border-gray-200 bg-gray-50">
                  <div className="p-6 space-y-6">
                    {studentResult.submissions.map((submission) => {
                      const evaluation = submission.evaluation!;
                      const questionPercentage = Math.round((evaluation.marks_awarded / evaluation.max_marks) * 100);

                      return (
                        <div 
                          key={submission.id} 
                          className="bg-white rounded-lg border border-gray-200 p-5 space-y-4"
                        >
                          {/* Question Header */}
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="text-lg font-semibold text-gray-900">
                                Question #{submission.question_id}
                              </h4>
                              <p className="text-sm text-gray-500">
                                Submitted on {new Date(submission.submitted_at).toLocaleString()}
                              </p>
                            </div>
                            <div className="text-right">
                              <div className="flex items-center space-x-2">
                                <CheckCircle className="h-5 w-5 text-green-500" />
                                <span className={`text-xl font-bold ${
                                  questionPercentage >= 80 ? 'text-green-600' :
                                  questionPercentage >= 60 ? 'text-yellow-600' :
                                  'text-red-600'
                                }`}>
                                  {evaluation.marks_awarded} / {evaluation.max_marks}
                                </span>
                              </div>
                              <p className="text-sm text-gray-500 mt-1">
                                ({questionPercentage}%)
                              </p>
                            </div>
                          </div>

                          {/* Student Answer */}
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Student Answer:
                            </label>
                            <textarea
                              value={submission.extracted_text || 'No text extracted'}
                              readOnly
                              className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-900 text-sm focus:outline-none resize-none"
                              rows={4}
                            />
                          </div>

                          {/* AI Feedback */}
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              AI Feedback:
                            </label>
                            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                {evaluation.ai_feedback}
                              </p>
                            </div>
                          </div>

                          {/* Detailed Scores */}
                          {Object.keys(evaluation.detailed_scores).length > 0 && (
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                Score Breakdown:
                              </label>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {Object.entries(evaluation.detailed_scores).map(([criterion, score]) => (
                                  <div 
                                    key={criterion}
                                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                                  >
                                    <span className="text-sm font-medium text-gray-700 capitalize">
                                      {criterion.replace(/_/g, ' ')}
                                    </span>
                                    <span className="text-sm font-bold text-indigo-600">
                                      {score}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ViewResults;