import { useState, useEffect } from 'react';
import { CheckCircle, Eye, Clock } from 'lucide-react';
import EvaluationResults from '../components/EvaluationResults';
import Loading from '../components/Loading';
import { getAllEvaluationResults } from '../services/api';

// Define a type for results
interface Result {
  id: number;
  testTitle: string;
  subject: string;
  studentName: string;
  score: number;
  date: string;
  status: string;
}

const ViewResults: React.FC = () => {
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedResult, setSelectedResult] = useState<Result | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const resultsData: Result[] = await getAllEvaluationResults();
        setResults(resultsData);
      } catch (error) {
        console.error('Error fetching results:', error);
        // Fallback mock data
        setResults([
          { 
            id: 1, 
            testTitle: 'Math Midterm', 
            subject: 'Mathematics', 
            studentName: 'John Doe',
            score: 85, 
            date: '2024-01-15',
            status: 'completed'
          },
          { 
            id: 2, 
            testTitle: 'History Quiz', 
            subject: 'History', 
            studentName: 'Jane Smith',
            score: 92, 
            date: '2024-01-12',
            status: 'completed'
          },
          { 
            id: 3, 
            testTitle: 'Science Test', 
            subject: 'Physics', 
            studentName: 'Bob Johnson',
            score: 78, 
            date: '2024-01-10',
            status: 'completed'
          }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, []);

  if (loading) return <Loading />;

  if (selectedResult) {
    return (
      <EvaluationResults 
        result={selectedResult} 
        onBack={() => setSelectedResult(null)} 
      />
    );
  }

  const averageScore = results.length > 0
    ? Math.round(results.reduce((sum, result) => sum + result.score, 0) / results.length)
    : 0;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="bg-gradient-to-r from-blue-500 to-cyan-600 px-6 py-4 rounded-t-xl">
          <h2 className="text-lg font-semibold text-white">Evaluation Results</h2>
        </div>
        <div className="p-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center">
                <CheckCircle className="h-8 w-8 text-green-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800">Average Score</p>
                  <p className="text-2xl font-bold text-green-900">{averageScore}%</p>
                </div>
              </div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center">
                <Eye className="h-8 w-8 text-blue-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-blue-800">Tests Evaluated</p>
                  <p className="text-2xl font-bold text-blue-900">{results.length}</p>
                </div>
              </div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="flex items-center">
                <Clock className="h-8 w-8 text-yellow-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-yellow-800">Avg. Time</p>
                  <p className="text-2xl font-bold text-yellow-900">2.3s</p>
                </div>
              </div>
            </div>
          </div>

          {/* Results List */}
          <div className="space-y-4">
            {results.map(result => (
              <div 
                key={result.id} 
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">{result.testTitle}</h3>
                    <p className="text-sm text-gray-500">
                      {result.subject} • {result.studentName} • Evaluated on {result.date}
                    </p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                      result.score >= 90 ? 'bg-green-100 text-green-800' :
                      result.score >= 75 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {result.score}%
                    </span>
                    <button
                      onClick={() => setSelectedResult(result)}
                      className="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {results.length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500">No evaluation results found.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ViewResults;
