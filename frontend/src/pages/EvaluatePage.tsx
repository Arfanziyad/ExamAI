import React, { useState } from 'react';
import { Settings, FileText, User, ChevronDown } from 'lucide-react';

const EvaluatePage = () => {
  const [similarityThreshold, setSimilarityThreshold] = useState(50);
  const [evaluationModel, setEvaluationModel] = useState('Semantic Similarity');
  const [subjectArea, setSubjectArea] = useState('General Knowledge');
  const [feedbackDetail, setFeedbackDetail] = useState('Detailed');
  const [referenceAnswer, setReferenceAnswer] = useState('');
  const [studentAnswer, setStudentAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleEvaluate = async () => {
    if (!referenceAnswer || !studentAnswer) {
      alert('Please enter both reference and student answers');
      return;
    }

    setLoading(true);
    try {
      // Here you would call your evaluation API
      // const result = await evaluateAnswers({
      //   referenceAnswer,
      //   studentAnswer,
      //   settings: {
      //     similarityThreshold,
      //     evaluationModel,
      //     subjectArea,
      //     feedbackDetail
      //   }
      // });
      
      setTimeout(() => {
        alert('Evaluation completed! Check results page.');
        setLoading(false);
      }, 2000);
    } catch (error) {
      console.error('Error evaluating answers:', error);
      alert('Error during evaluation. Please try again.');
      setLoading(false);
    }
  };

  const handleClear = () => {
    setReferenceAnswer('');
    setStudentAnswer('');
  };

  return (
    <div className="space-y-8">
      {/* Evaluation Settings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Evaluation Settings</h2>
          </div>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Similarity Threshold */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">
                Similarity Threshold
              </label>
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-500">
                  <span>Strict</span>
                  <span>Lenient</span>
                </div>
                <div className="relative">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={similarityThreshold}
                    onChange={(e) => setSimilarityThreshold(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    style={{
                      background: `linear-gradient(to right, #6366f1 0%, #6366f1 ${similarityThreshold}%, #e5e7eb ${similarityThreshold}%, #e5e7eb 100%)`
                    }}
                  />
                  <div 
                    className="absolute top-1/2 transform -translate-y-1/2 w-4 h-4 bg-indigo-600 rounded-full shadow-lg"
                    style={{ left: `calc(${similarityThreshold}% - 8px)` }}
                  />
                </div>
              </div>
            </div>

            {/* Other settings */}
            {[
              { 
                label: 'Evaluation Model', 
                value: evaluationModel, 
                setter: setEvaluationModel,
                options: ['Semantic Similarity', 'Keyword Matching', 'Deep Learning', 'Hybrid Approach']
              },
              { 
                label: 'Subject Area', 
                value: subjectArea, 
                setter: setSubjectArea,
                options: ['General Knowledge', 'Mathematics', 'Science', 'Literature', 'History', 'Computer Science']
              },
              { 
                label: 'Feedback Detail', 
                value: feedbackDetail, 
                setter: setFeedbackDetail,
                options: ['Detailed', 'Summary', 'Brief', 'Score Only']
              }
            ].map(({ label, value, setter, options }) => (
              <div key={label} className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">{label}</label>
                <div className="relative">
                  <select
                    value={value}
                    onChange={(e) => setter(e.target.value)}
                    className="block w-full pl-3 pr-10 py-2.5 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 rounded-lg bg-white"
                  >
                    {options.map(option => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Answer Input */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
          <div className="flex items-center space-x-2 text-white">
            <FileText className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Enter Answers for Evaluation</h2>
          </div>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Reference Answer */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2 mb-3">
                <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                  <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                </div>
                <h3 className="text-base font-medium text-gray-900">
                  Answer Scheme (Reference Answer)
                </h3>
              </div>
              <textarea
                value={referenceAnswer}
                onChange={(e) => setReferenceAnswer(e.target.value)}
                placeholder="Enter the reference answer or model solution here..."
                className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                rows={12}
              />
            </div>

            {/* Student Answer */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2 mb-3">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                  <User className="w-3 h-3 text-blue-600" />
                </div>
                <h3 className="text-base font-medium text-gray-900">
                  Student's Answer
                </h3>
              </div>
              <textarea
                value={studentAnswer}
                onChange={(e) => setStudentAnswer(e.target.value)}
                placeholder="Enter the student's answer here..."
                className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                rows={12}
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-center space-x-4 mt-8">
            <button
              onClick={handleEvaluate}
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium rounded-lg hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transform hover:scale-105 transition-all duration-200 shadow-lg disabled:opacity-50"
            >
              {loading ? 'Evaluating...' : 'Evaluate Answers'}
            </button>
            <button
              onClick={handleClear}
              className="px-6 py-3 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors duration-200"
            >
              Clear All
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvaluatePage;