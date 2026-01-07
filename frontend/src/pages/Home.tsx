import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, BookOpen, BarChart3, Upload, Zap } from 'lucide-react';
import { getTests } from '../services/api';

type Test = {
  id: number;
  title: string;
  subject: string;
  date: string;
};

const Home = () => {
  const [tests, setTests] = useState<Test[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTests = async () => {
      try {
        const testsData = await getTests();
        setTests(testsData);
      } catch (error) {
        console.error('Error fetching tests:', error);
        // Mock data fallback
        setTests([
          { id: 1, title: 'Math Midterm', subject: 'Mathematics', date: '2024-01-15' },
          { id: 2, title: 'History Quiz', subject: 'History', date: '2024-01-12' },
          { id: 3, title: 'Science Test', subject: 'Physics', date: '2024-01-10' }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchTests();
  }, []);

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 rounded-xl text-white p-8">
        <h1 className="text-3xl font-bold mb-4">Welcome to AI Exam Evaluator</h1>
        <p className="text-lg opacity-90 mb-6">Intelligent evaluation system for academic assessments with end-to-end automation</p>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Link
            to="/create"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 p-4 rounded-lg transition-all duration-200 text-left block"
          >
            <Plus className="h-6 w-6 mb-2" />
            <div className="font-semibold">Create Test</div>
            <div className="text-sm opacity-80">Manual test creation</div>
          </Link>
          <Link
            to="/create-advanced"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 p-4 rounded-lg transition-all duration-200 text-left block"
          >
            <Plus className="h-6 w-6 mb-2" />
            <div className="font-semibold">Advanced OCR</div>
            <div className="text-sm opacity-80">Multi-question detection</div>
          </Link>
          <Link
            to="/submit-multi"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 p-4 rounded-lg transition-all duration-200 text-left block"
          >
            <Zap className="h-6 w-6 mb-2" />
            <div className="font-semibold">Smart Submit</div>
            <div className="text-sm opacity-80">Auto-map & evaluate</div>
          </Link>
          <Link
            to="/take"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 p-4 rounded-lg transition-all duration-200 text-left block"
          >
            <BookOpen className="h-6 w-6 mb-2" />
            <div className="font-semibold">Take Test</div>
            <div className="text-sm opacity-80">Submit answers</div>
          </Link>
          <Link
            to="/results-aggregated"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 p-4 rounded-lg transition-all duration-200 text-left block"
          >
            <BarChart3 className="h-6 w-6 mb-2" />
            <div className="font-semibold">Analytics</div>
            <div className="text-sm opacity-80">Comprehensive results</div>
          </Link>
        </div>
      </div>

      {/* Recent Tests */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Tests</h2>
        </div>
        <div className="p-6">
          {loading ? (
            <div className="text-center py-4">Loading...</div>
          ) : (
            <div className="space-y-4">
              {tests.map(test => (
                <div key={test.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  <div>
                    <h3 className="font-medium text-gray-900">{test.title}</h3>
                    <p className="text-sm text-gray-500">{test.subject} • {test.date}</p>
                  </div>
                  <Link 
                    to={`/results/${test.id}`}
                    className="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                  >
                    View Details
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Home;