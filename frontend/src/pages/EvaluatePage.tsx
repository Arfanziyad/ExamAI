import { useState, useEffect } from 'react';
import { Settings, FileText, User, ChevronDown, Award, AlertCircle, CheckCircle2, Clock, Loader2 } from 'lucide-react';
import { getTests, getAllEvaluationResults, getORGroupSummary } from '../services/api';
import type { QuestionPaper, SubmissionData, ORGroupSummary } from '../types';

interface TestSubmission extends SubmissionData {
  question_text: string;
  answer_text: string;
  test_title: string;
}

const EvaluatePage = () => {
  const [tests, setTests] = useState<QuestionPaper[]>([]);
  const [selectedTestId, setSelectedTestId] = useState<number | null>(null);
  const [submissions, setSubmissions] = useState<TestSubmission[]>([]);
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [evaluatingSubmissions, setEvaluatingSubmissions] = useState<Set<number>>(new Set());
  const [ocrProcessingSubmissions, setOcrProcessingSubmissions] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  
  // OR Groups state
  const [orGroupSummaries, setOrGroupSummaries] = useState<Record<string, ORGroupSummary>>({});

  // Load available tests on component mount
  useEffect(() => {
    loadTests();
  }, []);

  // Load submissions when test is selected
  useEffect(() => {
    if (selectedTestId) {
      loadSubmissions();
    }
  }, [selectedTestId]);

  const loadTests = async () => {
    try {
      const testsData = await getTests();
      console.log('Tests loaded:', testsData);
      setTests(Array.isArray(testsData) ? testsData : []);
      setError(null);
    } catch (error) {
      console.error('Error loading tests:', error);
      setError(`Failed to load tests: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const loadSubmissions = async () => {
    if (!selectedTestId) return;
    
    setLoading(true);
    try {
      // Get all submissions
      const allSubmissions = await getAllEvaluationResults();
      console.log('All submissions received:', allSubmissions);
      
      // Get selected test details
      const selectedTest = tests.find(test => test.id === selectedTestId);
      if (!selectedTest) {
        setError('Selected test not found');
        setLoading(false);
        return;
      }
      
      console.log('Selected test:', selectedTest);
      console.log('Looking for submissions with question_id:', selectedTest.question_id);
      
      // Ensure allSubmissions is an array
      const submissionsArray = Array.isArray(allSubmissions) ? allSubmissions : [];
      
      // Filter submissions for the selected test's question_id
      const testSubmissions = submissionsArray
        .filter((sub: any) => {
          console.log('Checking submission:', sub.id, 'question_id:', sub.question_id, 'vs', selectedTest.question_id);
          return sub.question_id === selectedTest.question_id;
        })
        .map((sub: any) => ({
          ...sub,
          question_text: selectedTest.question_text,
          answer_text: selectedTest.answer_text,
          test_title: selectedTest.title
        }));
      
      console.log('Filtered submissions:', testSubmissions);
      setSubmissions(testSubmissions);
      
      // Load OR group summaries for each student
      await loadOrGroupSummaries(testSubmissions);
      
      setError(null);
    } catch (error) {
      console.error('Error loading submissions:', error);
      setError(`Failed to load submissions: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const loadOrGroupSummaries = async (submissions: TestSubmission[]) => {
    if (!selectedTestId) return;
    
    try {
      // Get unique student names
      const studentNames = [...new Set(submissions.map(sub => sub.student_name))];
      
      const summaries: Record<string, ORGroupSummary> = {};
      
      // Load OR group summary for each student
      for (const studentName of studentNames) {
        try {
          const response = await getORGroupSummary(selectedTestId, studentName);
          if (response.status === 'success') {
            summaries[studentName] = response.data;
          }
        } catch (error) {
          console.warn(`Failed to load OR group summary for ${studentName}:`, error);
          // Don't fail if OR groups aren't configured for this test
        }
      }
      
      setOrGroupSummaries(summaries);
    } catch (error) {
      console.error('Error loading OR group summaries:', error);
    }
  };

  const retryOcrForSubmission = async (submissionId: number) => {
    setOcrProcessingSubmissions(prev => new Set(prev).add(submissionId));
    try {
      const response = await fetch(`http://localhost:5000/api/submissions/${submissionId}/retry-ocr`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`OCR retry failed: ${response.status} ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('OCR retry result:', result);
      
      // Reload submissions to show updated OCR text
      await loadSubmissions();
      setError(null);
    } catch (error) {
      console.error('Error retrying OCR:', error);
      setError(`OCR retry failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setOcrProcessingSubmissions(prev => {
        const newSet = new Set(prev);
        newSet.delete(submissionId);
        return newSet;
      });
    }
  };

  const evaluateSubmission = async (submissionId: number) => {
    setEvaluatingSubmissions(prev => new Set(prev).add(submissionId));
    try {
      const response = await fetch(`http://localhost:5000/api/submissions/${submissionId}/evaluate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Evaluation failed: ${response.status} ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('Evaluation result:', result);
      
      // Reload submissions to show updated evaluation results
      await loadSubmissions();
      setError(null);
    } catch (error) {
      console.error('Error evaluating submission:', error);
      setError(`Evaluation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setEvaluatingSubmissions(prev => {
        const newSet = new Set(prev);
        newSet.delete(submissionId);
        return newSet;
      });
    }
  };

  const handleEvaluate = async () => {
    if (!selectedTestId) {
      setError('Please select a test first.');
      return;
    }

    setEvaluating(true);
    try {
      // Test API connectivity first
      console.log('Testing API connectivity...');
      
      // Refresh submissions to get latest evaluation data
      await loadSubmissions();
      setError(null);
    } catch (error) {
      console.error('Error evaluating submissions:', error);
      setError(`Error during evaluation: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setEvaluating(false);
    }
  };

  const testApiConnection = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/question-papers');
      console.log('API test response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('API test data:', data);
        setError(null);
      } else {
        setError(`API connection failed: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('API connection test failed:', error);
      setError(`API connection failed: ${error instanceof Error ? error.message : 'Network error'}`);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl shadow-lg p-6">
        <div className="flex items-center space-x-3 text-white">
          <Award className="h-8 w-8" />
          <div>
            <h1 className="text-2xl font-bold">Evaluate Test Submissions</h1>
            <p className="text-indigo-100 mt-1">Review student answers, model answers, and evaluation results</p>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Test Selection */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Select Test to Evaluate</h2>
          </div>
        </div>
        
        <div className="p-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Available Tests
              </label>
              <div className="relative">
                <select
                  value={selectedTestId || ''}
                  onChange={(e) => setSelectedTestId(e.target.value ? Number(e.target.value) : null)}
                  className="block w-full pl-3 pr-10 py-3 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 rounded-lg bg-white"
                >
                  <option value="">Select a test to evaluate...</option>
                  {tests.map(test => (
                    <option key={test.id} value={test.id}>
                      {test.title} - {test.subject} ({test.created_at ? new Date(test.created_at).toLocaleDateString() : 'No date'})
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {selectedTestId && (
              <div className="flex justify-center space-x-3">
                <button
                  onClick={handleEvaluate}
                  disabled={evaluating || loading}
                  className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium rounded-lg hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transform hover:scale-105 transition-all duration-200 shadow-lg disabled:opacity-50"
                >
                  {evaluating ? 'Refreshing Evaluations...' : loading ? 'Loading...' : 'Load & Evaluate Submissions'}
                </button>
                
                {submissions.length > 0 && (
                  <button
                    onClick={() => loadSubmissions()}
                    disabled={loading}
                    className="px-4 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors duration-200 disabled:opacity-50"
                  >
                    🔄 Refresh
                  </button>
                )}
                
                <button
                  onClick={testApiConnection}
                  disabled={loading}
                  className="px-4 py-3 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors duration-200 disabled:opacity-50"
                >
                  Test API
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Question and Model Answer Display */}
      {selectedTestId && !loading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="bg-gradient-to-r from-green-500 to-teal-600 px-6 py-4">
            <div className="flex items-center space-x-2 text-white">
              <FileText className="h-5 w-5" />
              <h2 className="text-lg font-semibold">Question & Model Answer</h2>
            </div>
          </div>
          
          {(() => {
            const selectedTest = tests.find(test => test.id === selectedTestId);
            if (!selectedTest) return null;
            
            return (
              <div className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Question */}
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2 mb-3">
                      <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                        <FileText className="w-3 h-3 text-blue-600" />
                      </div>
                      <h3 className="text-base font-medium text-gray-900">Question</h3>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-gray-800 whitespace-pre-wrap">{selectedTest.question_text}</p>
                    </div>
                  </div>

                  {/* Model Answer */}
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2 mb-3">
                      <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                        <CheckCircle2 className="w-3 h-3 text-green-600" />
                      </div>
                      <h3 className="text-base font-medium text-gray-900">Model Answer</h3>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <p className="text-gray-800 whitespace-pre-wrap">{selectedTest.answer_text}</p>
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      )}

      {/* Submissions and Evaluations */}
      {selectedTestId && !loading && submissions.length > 0 && (
        <div className="space-y-6">
          {/* Total Score Summary */}
          {(() => {
            const evaluatedSubmissions = submissions.filter(s => s.evaluation);
            if (evaluatedSubmissions.length === 0) return null;
            
            // Group submissions by student
            const studentScores = evaluatedSubmissions.reduce((acc, submission) => {
              const studentName = submission.student_name;
              if (!acc[studentName]) {
                acc[studentName] = {
                  totalMarks: 0,
                  maxMarks: 0,
                  submissions: []
                };
              }
              // We already filtered for submissions with evaluations, so this is safe
              const evaluation = submission.evaluation!;
              acc[studentName].totalMarks += evaluation.marks_awarded;
              acc[studentName].maxMarks += evaluation.max_marks;
              acc[studentName].submissions.push(submission);
              return acc;
            }, {} as Record<string, { totalMarks: number; maxMarks: number; submissions: typeof submissions }>);
            
            return (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-4">
                  <div className="flex items-center space-x-2 text-white">
                    <Award className="h-5 w-5" />
                    <h2 className="text-lg font-semibold">Total Score Summary</h2>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(studentScores).map(([studentName, scores]) => (
                      <div key={studentName} className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
                        <div className="text-center">
                          <h3 className="font-semibold text-gray-900 mb-2">{studentName}</h3>
                          <div className="text-3xl font-bold text-indigo-600 mb-1">
                            {scores.totalMarks} / {scores.maxMarks}
                          </div>
                          <div className="text-sm text-gray-600">
                            Total Score
                          </div>
                          <div className="mt-2 text-xs text-gray-500">
                            {scores.submissions.length} question{scores.submissions.length !== 1 ? 's' : ''} completed
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })()}
          
          {/* Individual Submissions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="bg-gradient-to-r from-purple-500 to-pink-600 px-6 py-4">
              <div className="flex items-center space-x-2 text-white">
                <User className="h-5 w-5" />
                <h2 className="text-lg font-semibold">Individual Question Results</h2>
                <span className="bg-white bg-opacity-20 px-2 py-1 rounded-full text-sm">
                  {submissions.length} submission{submissions.length !== 1 ? 's' : ''}
                </span>
              </div>
            </div>
          
          <div className="p-6 space-y-6">
            {submissions.map((submission, index) => (
              <div key={submission.id} className="border border-gray-200 rounded-lg overflow-hidden">
                {/* Submission Header */}
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-blue-600">{index + 1}</span>
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{submission.student_name}</h3>
                        <p className="text-sm text-gray-500">
                          Submitted: {new Date(submission.submitted_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    
                    {/* Evaluation Status */}
                    {submission.evaluation ? (
                      <div className="flex items-center space-x-2">
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                        <span className="text-sm font-medium text-green-600">Evaluated</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <Clock className="h-5 w-5 text-orange-500" />
                        <span className="text-sm font-medium text-orange-500">Pending Evaluation</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* OR Group Information */}
                {(() => {
                  const studentSummary = orGroupSummaries[submission.student_name];
                  if (!studentSummary || Object.keys(studentSummary.or_groups).length === 0) return null;
                  
                  return (
                    <div className="bg-purple-50 border-l-4 border-purple-400 px-4 py-3">
                      <div className="flex items-center space-x-2 mb-2">
                        <Settings className="h-4 w-4 text-purple-600" />
                        <span className="text-sm font-medium text-purple-900">OR Groups Status</span>
                      </div>
                      <div className="space-y-2">
                        {Object.entries(studentSummary.or_groups).map(([groupId, group]) => (
                          <div key={groupId} className="text-sm">
                            <div className="font-medium text-purple-800">{group.title}</div>
                            <div className="text-purple-600">
                              Attempted: {group.attempted_questions.length} of {group.questions.length} questions
                              ({group.earned_marks}/{group.total_possible_marks} marks)
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })()}

                <div className="p-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Student Answer */}
                    <div className="space-y-3">
                      <h4 className="font-medium text-gray-900">Student's Answer</h4>
                      
                      {submission.extracted_text && submission.extracted_text.trim().length > 0 ? (
                        <div className="bg-blue-50 rounded-lg p-4">
                          <p className="text-gray-800 whitespace-pre-wrap">{submission.extracted_text}</p>
                          {submission.ocr_confidence && (
                            <div className="mt-2 text-xs text-gray-500">
                              OCR Confidence: {(submission.ocr_confidence * 100).toFixed(1)}%
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-center">
                          <div className="text-orange-800">
                            <p className="font-medium">OCR Processing Issue</p>
                            <p className="text-sm mt-1">
                              {submission.extracted_text === "" ? 
                                "OCR returned empty text - the image might be unclear or processing failed" :
                                submission.extracted_text === null ? 
                                "OCR processing not started yet" :
                                "OCR data not available"
                              }
                            </p>
                            <button
                              onClick={() => retryOcrForSubmission(submission.id)}
                              disabled={ocrProcessingSubmissions.has(submission.id)}
                              className="mt-2 px-3 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                            >
                              {ocrProcessingSubmissions.has(submission.id) ? (
                                <>
                                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                  Processing OCR...
                                </>
                              ) : (
                                <>🔄 Retry OCR</>
                              )}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Evaluation Results */}
                    <div className="space-y-3">
                      <h4 className="font-medium text-gray-900">Evaluation Results</h4>
                      {submission.evaluation ? (
                        <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg p-4">
                          {/* Score Display */}
                          <div className="flex items-center justify-between mb-4">
                            <div className="text-2xl font-bold text-gray-900">
                              {submission.evaluation.marks_awarded} / {submission.evaluation.max_marks}
                            </div>
                            <div className="text-right">
                              <div className="text-sm text-gray-600">Similarity Score</div>
                              <div className="text-lg font-semibold text-indigo-600">
                                {(submission.evaluation.similarity_score * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>

                          {/* Detailed Scores */}
                          {submission.evaluation.detailed_scores && Object.keys(submission.evaluation.detailed_scores).length > 0 && (
                            <div className="mb-4">
                              <h5 className="text-sm font-medium text-gray-700 mb-2">Detailed Breakdown</h5>
                              <div className="space-y-1">
                                {Object.entries(submission.evaluation.detailed_scores).map(([criterion, score]) => (
                                  <div key={criterion} className="flex justify-between text-sm">
                                    <span className="text-gray-600 capitalize">{criterion.replace('_', ' ')}</span>
                                    <span className="font-medium">{score}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* AI Feedback */}
                          {submission.evaluation.ai_feedback && (
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-2">AI Feedback</h5>
                              <p className="text-sm text-gray-800 bg-white rounded p-3">
                                {submission.evaluation.ai_feedback}
                              </p>
                            </div>
                          )}

                          <div className="mt-3 flex justify-between items-center">
                            <div className="text-xs text-gray-500">
                              Evaluated: {new Date(submission.evaluation.created_at).toLocaleString()}
                            </div>
                            <button
                              onClick={() => evaluateSubmission(submission.id)}
                              disabled={evaluatingSubmissions.has(submission.id)}
                              className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                            >
                              {evaluatingSubmissions.has(submission.id) ? (
                                <>
                                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                  Re-evaluating...
                                </>
                              ) : (
                                <>🔄 Re-evaluate</>
                              )}
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-orange-50 rounded-lg p-4 text-center">
                          <Clock className="h-8 w-8 text-orange-500 mx-auto mb-2" />
                          <p className="text-orange-800">Evaluation pending</p>
                          <p className="text-sm text-orange-600 mt-1">
                            This submission hasn't been evaluated yet
                          </p>
                          <button
                            onClick={() => evaluateSubmission(submission.id)}
                            disabled={evaluatingSubmissions.has(submission.id)}
                            className="mt-3 px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                          >
                            {evaluatingSubmissions.has(submission.id) ? (
                              <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Evaluating...
                              </>
                            ) : (
                              <>📊 Start Evaluation</>
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        </div>
      )}

      {/* No Submissions Message */}
      {selectedTestId && !loading && submissions.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-12 text-center">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Submissions Found</h3>
            <p className="text-gray-600 mb-4">
              There are no student submissions for this test yet. Students need to submit their answers first.
            </p>
            <div className="text-sm text-gray-500">
              <p>Test ID: {selectedTestId}</p>
              {(() => {
                const selectedTest = tests.find(test => test.id === selectedTestId);
                return selectedTest && (
                  <div className="mt-2">
                    <p>Question ID: {selectedTest.question_id}</p>
                    <p>Total tests available: {tests.length}</p>
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvaluatePage;