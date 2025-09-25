import React, { useState } from 'react';
import FileUpload from './FileUpload';
import Loading from './Loading';
import { submitAnswer } from '../services/api';

interface AnswerSubmissionProps {
  questionId: number; // Change from string to number to match backend
  onSubmissionComplete: () => void;
}

const AnswerSubmission: React.FC<AnswerSubmissionProps> = ({ questionId, onSubmissionComplete }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [studentName, setStudentName] = useState('Anonymous');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = async (file: File | null) => {
    setSelectedFile(file); // update preview
    if (!file) return; // stop if user removed file

    try {
      setLoading(true);
      setError('');

      // Create FormData for Option 1
      const formData = new FormData();
      formData.append('file', file);
      formData.append('student_name', studentName);
      formData.append('question_id', questionId.toString()); // Convert number to string

      await submitAnswer(formData); // single argument
      onSubmissionComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit answer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <input
        className="w-full border rounded px-3 py-2"
        placeholder="Your name"
        value={studentName}
        onChange={(e) => setStudentName(e.target.value)}
      />
      <FileUpload
        onFileSelect={handleFileSelect}
        acceptedTypes=".jpg,.jpeg,.png,.pdf"
        label="Upload your handwritten answer"
        selectedFile={selectedFile}
      />
      {loading && <Loading />}
      {error && <p className="text-red-500">{error}</p>}
    </div>
  );
};

export default AnswerSubmission;
