import React, { useState } from 'react';
import Loading from '../components/Loading';

const CreateTest = () => {
  const [testTitle, setTestTitle] = useState('');
  const [testSubject, setTestSubject] = useState('');
  const [testDescription, setTestDescription] = useState('');
  const [questionText, setQuestionText] = useState('');
  const [answerText, setAnswerText] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    if (!testTitle || !testSubject || !questionText || !answerText) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('title', testTitle);
      formData.append('subject', testSubject);
      formData.append('description', testDescription);
      formData.append('question_text', questionText);
      formData.append('answer_text', answerText);

      const response = await fetch('http://localhost:8000/api/question-papers', {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to create test');
      }

      setSuccess(true);
    } catch (error) {
      console.error('Error creating test:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setError(`Error creating test: ${errorMessage}. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setTestTitle('');
    setTestSubject('');
    setTestDescription('');
    setQuestionText('');
    setAnswerText('');
    setSuccess(false);
    setError('');
  };

  if (loading) return <Loading />;

  if (success) {
    return (
      <div className="text-center">
        <div className="mb-4 text-green-600">
          <h2 className="text-2xl font-bold">Test Created Successfully!</h2>
        </div>
        <button
          onClick={handleReset}
          className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
        >
          Create Another Test
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Create New Test</h1>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block">
              <span className="text-gray-700">Test Title</span>
              <input
                type="text"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                value={testTitle}
                onChange={(e) => setTestTitle(e.target.value)}
                required
              />
            </label>
          </div>

          <div>
            <label className="block">
              <span className="text-gray-700">Subject</span>
              <input
                type="text"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                value={testSubject}
                onChange={(e) => setTestSubject(e.target.value)}
                required
              />
            </label>
          </div>
        </div>

        <div>
          <label className="block">
            <span className="text-gray-700">Description (Optional)</span>
            <textarea
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              rows={3}
              value={testDescription}
              onChange={(e) => setTestDescription(e.target.value)}
            />
          </label>
        </div>

        {/* Questions and Answers */}
        <div className="grid grid-cols-2 gap-8">
          {/* Question Text Input */}
          <div className="space-y-4">
            <label className="block">
              <span className="text-gray-700">Questions</span>
              <textarea
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                rows={10}
                placeholder="Enter test questions here..."
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                required
              />
            </label>
          </div>

          {/* Answer Key Text Input */}
          <div className="space-y-4">
            <label className="block">
              <span className="text-gray-700">Model Answers</span>
              <textarea
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                rows={10}
                placeholder="Enter model answers here..."
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                required
              />
            </label>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={handleReset}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Reset
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Create Test
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateTest;