import React, { useState, useEffect } from 'react';
import { Trophy, User, BarChart3, Target, Code, FileText } from 'lucide-react';
import { getTests, getStudentAggregatedScores } from '../services/api';

interface QuestionDetail {
  question_id: number;
  question_number: number;
  question_type: string;
  max_marks: number;
  question_text: string;
}

interface QuestionScore {
  question_id: number;
  question_number: number;
  question_type: string;
  marks_awarded: number;
  max_marks: number;
  submission_id: number;
}

interface StudentScore {
  student_name: string;
  total_marks: number;
  questions_attempted: number;
  questions_scored: QuestionScore[];
  question_types: {
    [key: string]: {
      total_marks: number;
      max_marks: number;
      count: number;
      percentage: number;
    };
  };
  rank: number;
  percentage: number;
}

interface AggregatedResults {
  question_paper_id: number;
  title: string;
  total_possible_marks: number;
  total_questions: number;
  question_details: QuestionDetail[];
  student_scores: StudentScore[];
  students_count: number;
}

const ViewAggregatedResults: React.FC = () => {
  const [tests, setTests] = useState<any[]>([]);
  const [selectedTest, setSelectedTest] = useState<number | null>(null);
  const [results, setResults] = useState<AggregatedResults | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchTests();
  }, []);

  const fetchTests = async () => {
    try {
      const testData = await getTests();
      setTests(testData);
    } catch (error) {
      console.error('Failed to fetch tests:', error);
    }
  };

  const fetchResults = async (testId: number) => {
    setLoading(true);
    try {
      const resultData = await getStudentAggregatedScores(testId);
      setResults(resultData);
    } catch (error) {
      console.error('Failed to fetch results:', error);
      alert('Failed to fetch results. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTestSelect = (testId: number) => {
    setSelectedTest(testId);
    fetchResults(testId);
  };

  const getTypeIcon = (type: string) => {
    return type === 'coding' ? <Code className="h-4 w-4" /> : <FileText className="h-4 w-4" />;
  };

  const getTypeColor = (type: string) => {
    return type === 'coding' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800';
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Aggregated Test Results
        </h1>
        <p className="text-gray-600">
          View comprehensive results and analytics for all students across multiple question types
        </p>
      </div>

      {/* Test Selection */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Select Test</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tests.map((test) => (
            <button
              key={test.id}
              onClick={() => handleTestSelect(test.id)}
              className={`p-4 text-left border rounded-lg hover:shadow-md transition-shadow ${
                selectedTest === test.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <h3 className="font-medium text-gray-900">{test.title}</h3>
              <p className="text-sm text-gray-600 mt-1">{test.subject}</p>
              <p className="text-xs text-gray-500 mt-2">
                Created: {new Date(test.created_at).toLocaleDateString()}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Results Display */}
      {loading && (
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <BarChart3 className="animate-spin h-8 w-8 mx-auto text-blue-600 mb-2" />
          <p>Loading results...</p>
        </div>
      )}

      {results && !loading && (
        <>
          {/* Summary Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <Target className="h-8 w-8 text-blue-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Questions</p>
                  <p className="text-2xl font-bold text-gray-900">{results.total_questions}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <User className="h-8 w-8 text-green-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Students</p>
                  <p className="text-2xl font-bold text-gray-900">{results.students_count}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <Trophy className="h-8 w-8 text-yellow-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Max Possible</p>
                  <p className="text-2xl font-bold text-gray-900">{results.total_possible_marks}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <BarChart3 className="h-8 w-8 text-purple-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Score</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {results.student_scores.length > 0
                      ? (
                          results.student_scores.reduce((sum, s) => sum + s.percentage, 0) /
                          results.student_scores.length
                        ).toFixed(1)
                      : 0}%
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Question Details */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Question Breakdown</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.question_details.map((question) => (
                <div key={question.question_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">Q{question.question_number}</span>
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(question.question_type)}`}>
                        {getTypeIcon(question.question_type)}
                        <span className="ml-1">{question.question_type}</span>
                      </span>
                      <span className="text-sm font-medium text-gray-600">
                        {question.max_marks} pts
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{question.question_text}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Student Rankings */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Student Rankings</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Student
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Percentage
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Subjective
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Coding
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Questions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {results.student_scores.map((student) => (
                    <tr key={student.student_name} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span className={`inline-flex items-center justify-center h-6 w-6 rounded-full text-xs font-medium ${
                            student.rank === 1 ? 'bg-yellow-100 text-yellow-800' :
                            student.rank === 2 ? 'bg-gray-100 text-gray-800' :
                            student.rank === 3 ? 'bg-orange-100 text-orange-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {student.rank}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {student.student_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {student.total_marks} / {results.total_possible_marks}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${Math.min(student.percentage, 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-900">
                            {student.percentage.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {student.question_types.subjective ? (
                          <span className="text-blue-600">
                            {student.question_types.subjective.percentage.toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {student.question_types.coding ? (
                          <span className="text-purple-600">
                            {student.question_types.coding.percentage.toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {student.questions_attempted} / {results.total_questions}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ViewAggregatedResults;