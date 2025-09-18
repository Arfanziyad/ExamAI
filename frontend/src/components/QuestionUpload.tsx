import React, { useState } from 'react';
import { uploadQuestions } from '../services';

interface QuestionUploadProps {
  onUploadStart?: () => void;
  onUploadComplete?: () => void;
  onUploadError?: () => void;
}

const QuestionUpload: React.FC<QuestionUploadProps> = ({
  onUploadStart,
  onUploadComplete,
  onUploadError
}) => {
  const [message, setMessage] = useState('');
  const [title, setTitle] = useState('Untitled Test');
  const [subject, setSubject] = useState('general');
  const [description, setDescription] = useState('');
  const [questionText, setQuestionText] = useState('');
  const [answerText, setAnswerText] = useState('');

  const handleSubmit = async () => {
    if (!questionText || !answerText) {
      setMessage('Please enter both question and answer text.');
      return;
    }
    try {
      onUploadStart?.();
      await uploadQuestions(questionText, answerText, title, subject, description);
      setMessage('Test created successfully!');
      onUploadComplete?.();
      // Clear the form
      setQuestionText('');
      setAnswerText('');
      setTitle('Untitled Test');
      setSubject('general');
      setDescription('');
    } catch (error) {
      setMessage('Error creating test. Please try again.');
      onUploadError?.();
      console.error('Error:', error);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Create Test</h2>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Test Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full border rounded px-3 py-2"
            placeholder="Enter test title"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Subject</label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full border rounded px-3 py-2"
            placeholder="Enter subject (e.g. science, math)"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Description (Optional)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full border rounded px-3 py-2 h-24"
            placeholder="Enter test description"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Questions</label>
          <textarea
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            className="w-full border rounded px-3 py-2 h-48"
            placeholder="Enter your questions here..."
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Answer Key</label>
          <textarea
            value={answerText}
            onChange={(e) => setAnswerText(e.target.value)}
            className="w-full border rounded px-3 py-2 h-48"
            placeholder="Enter the answer key here..."
          />
        </div>
      </div>

      <button
        onClick={handleSubmit}
        className="w-full bg-indigo-600 text-white py-2 px-4 rounded hover:bg-indigo-700 transition-colors"
        disabled={!questionText || !answerText}
      >
        Create Test
      </button>

      {message && (
        <div 
          className={`mt-4 p-4 rounded ${
            message.includes('Error') 
              ? 'bg-red-50 text-red-700 border border-red-300' 
              : 'bg-green-50 text-green-700 border border-green-300'
          }`}
        >
          {message}
        </div>
      )}
    </div>
  );
};

export default QuestionUpload;