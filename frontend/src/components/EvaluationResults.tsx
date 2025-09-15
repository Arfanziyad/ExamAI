import React from 'react';
import { ArrowLeft, Download, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface EvaluationResultsProps {
  result: any;
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
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Test Information</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <p><strong>Test:</strong> {result.testTitle}</p>
                <p><strong>Subject:</strong> {result.subject}</p>
                <p><strong>Student:</strong> {result.studentName}</p>
                <p><strong>Date:</strong> {result.date}</p>
              </div>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Score Breakdown</h3>
              <div className="flex items-center space-x-4">
                <div className="text-3xl font-bold text-indigo-600">{result.score}%</div>
                <div className="flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-indigo-600 h-3 rounded-full transition-all duration-1000"
                      style={{ width: `${result.score}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Detailed Feedback */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">Detailed Feedback</h3>
            
            {/* Mock detailed evaluation results */}
            <div className="space-y-3">
              <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium text-green-900">Strengths</p>
                  <p className="text-sm text-green-700">
                    Good understanding of core concepts. Clear explanations provided.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div>
                  <p className="font-medium text-yellow-900">Areas for Improvement</p>
                  <p className="text-sm text-yellow-700">
                    Some minor gaps in mathematical calculations. Consider showing more detailed steps.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                <div>
                  <p className="font-medium text-red-900">Missing Elements</p>
                  <p className="text-sm text-red-700">
                    Final conclusion could be more comprehensive.
                  </p>
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