import React, { useState } from 'react';
import FileUpload from './FileUpload';
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
  const [showTitleInput, setShowTitleInput] = useState(false);
  const [showSubjectInput, setShowSubjectInput] = useState(false);
  const [selectedQuestionFile, setSelectedQuestionFile] = useState<File | null>(null);
  const [selectedAnswerFile, setSelectedAnswerFile] = useState<File | null>(null);

  const handleQuestionFileSelect = (file: File | null) => {
    setSelectedQuestionFile(file);
  };

  const handleAnswerFileSelect = (file: File | null) => {
    setSelectedAnswerFile(file);
  };

  const handleSubmit = async () => {
    if (!selectedQuestionFile || !selectedAnswerFile) {
      setMessage('Please select both question paper and answer key files.');
      return;
    }
    try {
      onUploadStart?.();
      await uploadQuestions(selectedQuestionFile, selectedAnswerFile, title, subject, description);
      setMessage('Test uploaded successfully!');
      onUploadComplete?.();
      // Clear the form
      setSelectedQuestionFile(null);
      setSelectedAnswerFile(null);
      setTitle('Untitled Test');
      setSubject('general');
      setDescription('');
    } catch (error) {
      setMessage('Error uploading test. Please try again.');
      onUploadError?.();
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Upload Questions</h2>

      <div className="flex gap-3">
        <button
          onClick={() => setShowTitleInput(v => !v)}
          className="flex-1 py-2 px-3 bg-white border rounded-lg shadow-sm hover:shadow-md text-left"
        >
          <div className="text-xs text-gray-500">Test Title</div>
          <div className="text-sm font-medium">{title}</div>
        </button>

        <button
          onClick={() => setShowSubjectInput(v => !v)}
          className="w-40 py-2 px-3 bg-white border rounded-lg shadow-sm hover:shadow-md text-left"
        >
          <div className="text-xs text-gray-500">Subject</div>
          <div className="text-sm font-medium capitalize">{subject}</div>
        </button>
      </div>

      {showTitleInput && (
        <input
          className="w-full border rounded px-3 py-2"
          placeholder="Test title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      )}

      {showSubjectInput && (
        <input
          className="w-full border rounded px-3 py-2"
          placeholder="Subject (e.g. science, math)"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
        />
      )}

      <textarea
        className="w-full border rounded px-3 py-2"
        placeholder="Description (optional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />

      <FileUpload
        onFileSelect={handleQuestionFileSelect}
        acceptedTypes=".pdf,.doc,.docx,.jpg,.jpeg,.png"
        label="Select question paper file"
        selectedFile={selectedQuestionFile}
      />

      <FileUpload
        onFileSelect={handleAnswerFileSelect}
        acceptedTypes=".pdf,.doc,.docx,.jpg,.jpeg,.png"
        label="Select model answer file"
        selectedFile={selectedAnswerFile}
      />

      <button
        onClick={handleSubmit}
        className="w-full bg-indigo-600 text-white py-2 px-4 rounded hover:bg-indigo-700 transition-colors"
      >
        Upload Files
      </button>

      {message && <p className="text-green-600">{message}</p>}
    </div>
  );
};

export default QuestionUpload;
