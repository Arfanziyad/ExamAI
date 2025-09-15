import React, { useState, useEffect } from 'react';
import FileUpload from '../components/FileUpload';
import Loading from '../components/Loading';
import { getTests, submitAnswer } from '../services/api';

type Test = {
  id: string;
  title: string;
  subject: string;
};

const TakeTest: React.FC = () => {
  const [tests, setTests] = useState<Test[]>([]);
  const [selectedTest, setSelectedTest] = useState('');
  const [studentName, setStudentName] = useState('');
  const [answerFile, setAnswerFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Fetch all available tests
  useEffect(() => {
    const fetchTests = async () => {
      try {
        const testsData: Test[] = await getTests();
        setTests(testsData);
      } catch (error) {
        console.error('Error fetching tests:', error);
      }
    };
    fetchTests();
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!selectedTest || !studentName || !answerFile) {
      alert('Please fill all fields and select an answer file');
      return;
    }

    setLoading(true);
    try {
      // Build FormData as required by the API
      const formData = new FormData();
      formData.append('file', answerFile);
      formData.append('student_name', studentName);
      formData.append('question_id', selectedTest);

      await submitAnswer(formData);

      setSuccess(true);

      // Reset form
      setSelectedTest('');
      setStudentName('');
      setAnswerFile(null);
    } catch (error) {
      console.error('Error submitting answer:', error);
      alert('Error submitting answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="max-w-2xl mx-auto py-8">
      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800">Answer submitted successfully!</p>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="bg-gradient-to-r from-green-500 to-teal-600 px-6 py-4 rounded-t-xl">
          <h2 className="text-lg font-semibold text-white">Submit Test Answer</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Test Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Test *
            </label>
            <select
              value={selectedTest}
              onChange={(e) => setSelectedTest(e.target.value)}
              className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              required
            >
              <option value="">Choose a test</option>
              {tests.map((test) => (
                <option key={test.id} value={test.id}>
                  {test.title} - {test.subject}
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
              className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              placeholder="Enter your name"
              required
            />
          </div>

          {/* File Upload */}
          <FileUpload
            label="Upload Answer Sheet *"
            acceptedTypes=".pdf,.jpg,.jpeg,.png"
            onFileSelect={setAnswerFile}
            selectedFile={answerFile}
          />

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-green-600 to-teal-600 text-white font-medium py-3 rounded-lg hover:from-green-700 hover:to-teal-700 transition-all duration-200 disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Submit Answer'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default TakeTest;
