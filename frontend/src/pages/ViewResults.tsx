import { useState, useEffect } from 'react';
import { CheckCircle, Eye, Clock } from 'lucide-react';
import EvaluationResults from '../components/EvaluationResults';
import Loading from '../components/Loading';
import { getAllEvaluationResults } from '../services/api';

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
  student_name: string;
  handwriting_image_path: string;
  extracted_text?: string;
  ocr_confidence?: number;
  submitted_at: string;
  evaluation?: EvaluationData;
}

// Format submission data for the EvaluationResults component
interface FormattedResult {
  id: number;
  student_name: string;
  evaluation: {
    similarity_score: number;
    marks_awarded: number;
    max_marks: number;
    detailed_scores: Record<string, number>;
    ai_feedback: string;
    evaluation_time: string;
  };
}

const ViewResults: React.FC = () => {
  const [results, setResults] = useState<SubmissionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedResult, setSelectedResult] = useState<FormattedResult | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const submissionsData: SubmissionData[] = await getAllEvaluationResults();
        // Filter out submissions without evaluations
        const evaluatedSubmissions = submissionsData.filter(submission => submission.evaluation);
        setResults(evaluatedSubmissions);
      } catch (error) {
        console.error('Error fetching results:', error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, []);

  const handleViewResult = (submission: SubmissionData) => {
    if (submission.evaluation) {
      const formattedResult: FormattedResult = {
        id: submission.id,
        student_name: submission.student_name,
        evaluation: submission.evaluation
      };
      setSelectedResult(formattedResult);
    }
  };

  const handleBack = () => {
    setSelectedResult(null);
  };

  if (loading) return <Loading />;

  if (selectedResult) {
    return <EvaluationResults result={selectedResult} onBack={handleBack} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Evaluation Results</h1>
        <p className="text-gray-600">View and analyze student performance</p>
      </div>

      {/* Results Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">All Submissions</h2>
        </div>
        
        {results.length === 0 ? (
          <div className="p-8 text-center">
            <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No evaluation results available yet.</p>
            <p className="text-sm text-gray-400 mt-1">
              Submit some test answers to see evaluation results here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Student
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Submitted
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.map((submission) => {
                  const evaluation = submission.evaluation!;
                  const percentage = Math.round((evaluation.marks_awarded / evaluation.max_marks) * 100);
                  const submittedDate = new Date(submission.submitted_at).toLocaleDateString();
                  
                  return (
                    <tr key={submission.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {submission.student_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              Question #{submission.question_id}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className={`text-2xl font-bold ${
                            percentage >= 80 ? 'text-green-600' :
                            percentage >= 60 ? 'text-yellow-600' :
                            'text-red-600'
                          }`}>
                            {percentage}%
                          </div>
                          <div className="ml-2 text-sm text-gray-500">
                            ({evaluation.marks_awarded}/{evaluation.max_marks})
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {submittedDate}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <CheckCircle className="w-4 h-4 mr-1" />
                          Evaluated
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleViewResult(submission)}
                          className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ViewResults;