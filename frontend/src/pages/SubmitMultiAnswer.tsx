import React, { useState, useEffect } from 'react';
import Loading from '../components/Loading';
import FileUpload from '../components/FileUpload';
import { Upload, CheckCircle, FileText, Clock, AlertCircle } from 'lucide-react';

interface QuestionPaper {
  id: number;
  title: string;
  subject: string;
  description: string;
  created_at: string;
}

interface SubmissionResult {
  submission_id: number;
  question_number: number;
  question_text: string;
  extracted_answer: string;
  marks_awarded: number;
  max_marks: number;
  evaluation?: {
    similarity_score: number;
    ai_feedback: string;
  };
  error?: string;
}

interface MultiSubmissionResponse {
  success: boolean;
  message: string;
  student_name: string;
  question_paper_title: string;
  total_marks_awarded: number;
  total_possible_marks: number;
  percentage: number;
  submissions: SubmissionResult[];
  sequence_analysis: {
    detected_sequence: string[];
    confidence: number;
  };
  ocr_info: {
    confidence: number;
    extracted_text_preview: string;
  };
}

const SubmitMultiAnswer: React.FC = () => {
  const [questionPapers, setQuestionPapers] = useState<QuestionPaper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<number | null>(null);
  const [studentName, setStudentName] = useState('');
  const [answerFile, setAnswerFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<MultiSubmissionResponse | null>(null);
  const [error, setError] = useState('');

  // Fetch available question papers
  useEffect(() => {
    const fetchQuestionPapers = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/question-papers');
        if (!response.ok) {
          throw new Error('Failed to fetch question papers');
        }
        const papers = await response.json();
        setQuestionPapers(papers);
      } catch (error) {
        console.error('Error fetching question papers:', error);
        setError('Failed to load question papers. Please refresh the page.');
      }
    };

    fetchQuestionPapers();
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!selectedPaper || !studentName || !answerFile) {
      setError('Please fill all fields and select an answer file');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', answerFile);
      formData.append('student_name', studentName);

      const response = await fetch(`http://localhost:5000/api/question-papers/${selectedPaper}/submissions`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Submission failed: ${response.status} ${errorText}`);
      }

      const result: MultiSubmissionResponse = await response.json();
      setSubmissionResult(result);
      
      // Reset form
      setSelectedPaper(null);
      setStudentName('');
      setAnswerFile(null);

    } catch (error) {
      console.error('Error submitting answer:', error);
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loading />
          <div className="mt-4 space-y-2">
            <p className="text-lg font-medium text-gray-900">Processing Your Submission...</p>
            <p className="text-sm text-gray-600">• Extracting text from your answer sheet</p>
            <p className="text-sm text-gray-600">• Mapping answers to questions automatically</p>
            <p className="text-sm text-gray-600">• Evaluating each answer with AI</p>
            <p className="text-sm text-gray-600">• Calculating total marks</p>
            <div className="text-xs text-gray-500 mt-2">This may take 30-60 seconds...</div>
          </div>
        </div>
      </div>
    );
  }

  // Success page with detailed results
  if (submissionResult) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Success Header */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
            <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-6 rounded-t-xl">
              <div className="flex items-center">
                <CheckCircle className="h-8 w-8 text-white mr-3" />
                <div>
                  <h1 className="text-2xl font-bold text-white">{submissionResult.message}</h1>
                  <p className="text-green-100">All answers processed and evaluated successfully</p>
                </div>
              </div>
            </div>
            
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{submissionResult.student_name}</div>
                  <div className="text-sm text-gray-500">Student</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{submissionResult.question_paper_title}</div>
                  <div className="text-sm text-gray-500">Question Paper</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {submissionResult.total_marks_awarded}/{submissionResult.total_possible_marks}
                  </div>
                  <div className="text-sm text-gray-500">Total Marks</div>
                </div>
                <div className="text-center">
                  <div className={`text-3xl font-bold ${
                    submissionResult.percentage >= 90 ? 'text-green-600' :
                    submissionResult.percentage >= 75 ? 'text-blue-600' :
                    submissionResult.percentage >= 60 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {submissionResult.percentage}%
                  </div>
                  <div className="text-sm text-gray-500">Score</div>
                </div>
              </div>
            </div>
          </div>

          {/* OCR & Analysis Info */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-8 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Processing Summary
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">OCR Confidence</div>
                <div className={`text-2xl font-bold ${
                  submissionResult.ocr_info.confidence >= 0.9 ? 'text-green-600' :
                  submissionResult.ocr_info.confidence >= 0.7 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {Math.round(submissionResult.ocr_info.confidence * 100)}%
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">Answer Sequence Detection</div>
                <div className={`text-2xl font-bold ${
                  submissionResult.sequence_analysis.confidence >= 0.8 ? 'text-green-600' :
                  submissionResult.sequence_analysis.confidence >= 0.6 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {Math.round(submissionResult.sequence_analysis.confidence * 100)}%
                </div>
              </div>
            </div>
            
            {submissionResult.sequence_analysis.detected_sequence.length > 0 && (
              <div className="mt-4">
                <div className="text-sm font-medium text-gray-700 mb-2">Detected Answer Order</div>
                <div className="text-sm text-gray-600">
                  Questions answered in order: {submissionResult.sequence_analysis.detected_sequence.join(' → ')}
                </div>
              </div>
            )}
          </div>

          {/* Detailed Results */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Question-wise Results</h2>
            </div>
            
            <div className="divide-y divide-gray-200">
              {submissionResult.submissions.map((submission) => (
                <div key={submission.submission_id} className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-3">
                          Question {submission.question_number}
                        </span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          submission.marks_awarded === submission.max_marks ? 'bg-green-100 text-green-800' :
                          submission.marks_awarded >= submission.max_marks * 0.7 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {submission.marks_awarded}/{submission.max_marks} marks
                        </span>
                      </div>
                      <p className="text-sm text-gray-900 font-medium mb-2">{submission.question_text}</p>
                      
                      {submission.evaluation ? (
                        <div className="space-y-2">
                          <div className="text-xs text-gray-600">
                            <strong>Your Answer:</strong> {submission.extracted_answer}
                          </div>
                          <div className="text-xs text-gray-600">
                            <strong>AI Feedback:</strong> {submission.evaluation.ai_feedback}
                          </div>
                          <div className="text-xs text-gray-500">
                            Similarity Score: {Math.round(submission.evaluation.similarity_score * 100)}%
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center text-sm text-red-600">
                          <AlertCircle className="h-4 w-4 mr-1" />
                          {submission.error || 'Evaluation failed'}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-8 flex justify-center space-x-4">
            <button
              onClick={() => {
                setSubmissionResult(null);
                setError('');
              }}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Submit Another Answer
            </button>
            <button
              onClick={() => window.print()}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Print Results
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Submission form
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-6 rounded-t-xl">
            <div className="flex items-center">
              <Upload className="h-6 w-6 text-white mr-3" />
              <div>
                <h1 className="text-xl font-bold text-white">Submit Answer Sheet</h1>
                <p className="text-blue-100 text-sm">Upload your complete answer sheet for automatic processing</p>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
                  <span className="text-red-800">{error}</span>
                </div>
              </div>
            )}

            {/* Question Paper Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Question Paper *
              </label>
              <select
                value={selectedPaper || ''}
                onChange={(e) => setSelectedPaper(Number(e.target.value))}
                className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Choose a question paper...</option>
                {questionPapers.map((paper) => (
                  <option key={paper.id} value={paper.id}>
                    {paper.title} - {paper.subject}
                  </option>
                ))}
              </select>
            </div>

            {/* Student Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Student Name *
              </label>
              <input
                type="text"
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your full name"
                required
              />
            </div>

            {/* File Upload */}
            <FileUpload
              label="Upload Complete Answer Sheet *"
              acceptedTypes=".pdf,.jpg,.jpeg,.png"
              onFileSelect={setAnswerFile}
              selectedFile={answerFile}
            />

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <Clock className="h-5 w-5 text-blue-600 mr-2 mt-0.5" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">What happens next:</p>
                  <ul className="list-disc list-inside space-y-1 text-blue-700">
                    <li>Your answer sheet will be processed with OCR technology</li>
                    <li>Answers will be automatically mapped to questions</li>
                    <li>Each answer will be evaluated using AI</li>
                    <li>You'll receive instant detailed results and feedback</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!selectedPaper || !studentName || !answerFile}
              className="w-full flex items-center justify-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Upload className="h-5 w-5 mr-2" />
              Submit Answer Sheet
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default SubmitMultiAnswer;