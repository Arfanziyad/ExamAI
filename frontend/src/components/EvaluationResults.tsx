import React from 'react';
import { ArrowLeft, Download } from 'lucide-react';

interface EvaluationResultsProps {
  result: {
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
  };
  onBack: () => void;
}

const EvaluationResults: React.FC<EvaluationResultsProps> = ({ result, onBack }) => {
  const handleDownload = () => {
    // Implement download functionality
    console.log('Download result for:', result.id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-indigo-600 hover:text-indigo-700"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Results</span>
        </button>
        <button
          onClick={handleDownload}
          className="flex items-center space-x-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Download className="h-4 w-4" />
          <span>Download Report</span>
        </button>
      </div>

      {/* Result Overview */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="bg-gradient-to-r from-blue-500 to-cyan-600 px-6 py-4 rounded-t-xl">
          <h2 className="text-lg font-semibold text-white">Evaluation Details</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Test Information */}
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Test Information</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <p><strong>Student:</strong> {result.student_name}</p>
                <p><strong>Date:</strong> {new Date(result.evaluation.evaluation_time).toLocaleDateString()}</p>
              </div>
            </div>

            {/* Score Overview */}
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Score Breakdown</h3>
              <div className="flex items-center space-x-4">
                <div className="text-3xl font-bold text-indigo-600">
                  {Math.round((result.evaluation.marks_awarded / result.evaluation.max_marks) * 100)}%
                </div>
                <div className="flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-indigo-600 h-3 rounded-full transition-all duration-1000"
                      style={{ width: `${Math.round((result.evaluation.marks_awarded / result.evaluation.max_marks) * 100)}%` }}
                    ></div>
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {result.evaluation.marks_awarded} / {result.evaluation.max_marks} points
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* AI Feedback */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">AI Feedback</h3>
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <pre className="whitespace-pre-wrap text-sm text-gray-700">
                {result.evaluation.ai_feedback}
              </pre>
            </div>

            {/* Detailed Scores */}
            <h3 className="font-medium text-gray-900 mt-6">Score Analysis</h3>
            <div className="space-y-3">
              {Object.entries(result.evaluation.detailed_scores).map(([criterion, score]) => (
                <div key={criterion} className="flex items-start space-x-3 p-3 bg-white rounded-lg border border-gray-200">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{criterion}</p>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                      <div 
                        className="bg-indigo-600 h-2 rounded-full transition-all duration-1000"
                        style={{ width: `${score * 100}%` }}
                      />
                    </div>
                  </div>
                  <div className="text-sm font-medium text-gray-600">
                    {Math.round(score * 100)}%
                  </div>
                </div>
              ))}

              {/* Similarity Score */}
              <div className="flex items-start space-x-3 p-3 bg-white rounded-lg border border-gray-200">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">Overall Similarity</p>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-1000"
                      style={{ width: `${result.evaluation.similarity_score * 100}%` }}
                    />
                  </div>
                </div>
                <div className="text-sm font-medium text-gray-600">
                  {Math.round(result.evaluation.similarity_score * 100)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvaluationResults;