import React, { useState } from 'react';
import FileUpload from '../components/FileUpload';
import Loading from '../components/Loading';
import OCRVerification from '../components/OCRVerification';
import OCRStatus from '../components/OCRStatus';
import { uploadQuestions, verifyOCRText } from '../services';
import type { OCRResult } from '../services';

const CreateTest = () => {
  const [testTitle, setTestTitle] = useState('');
  const [testSubject, setTestSubject] = useState('');
  const [testDescription, setTestDescription] = useState('');
  const [questionFile, setQuestionFile] = useState<File | null>(null);
  const [answerFile, setAnswerFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [paperId, setPaperId] = useState<string>('');
  const [ocrStatus, setOcrStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [questionOCR, setQuestionOCR] = useState<OCRResult | null>(null);
  const [answerOCR, setAnswerOCR] = useState<OCRResult | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    if (!testTitle || !testSubject) {
      setError('Please fill in all required fields');
      return;
    }

    if (!questionFile || !answerFile) {
      setError('Please select both question paper and model answer files');
      return;
    }

    setLoading(true);
    setOcrStatus('processing');
    try {
      const result = await uploadQuestions(
        questionFile,
        answerFile,
        testTitle,
        testSubject,
        testDescription
      );
      
      setPaperId(result.id);
      setQuestionOCR(result.questionOCR);
      setAnswerOCR(result.answerOCR);
      setOcrStatus('success');
      
    } catch (error) {
      console.error('Error creating test:', error);
      setError('Error creating test. Please try again.');
      setOcrStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyQuestion = async (correctedText: string) => {
    if (!paperId) return;
    try {
      await verifyOCRText(paperId, 'question', correctedText);
      setQuestionOCR(prev => prev ? { ...prev, extracted_text: correctedText } : null);
    } catch (error) {
      console.error('Error verifying question OCR:', error);
      setError('Error updating OCR text. Please try again.');
    }
  };

  const handleVerifyAnswer = async (correctedText: string) => {
    if (!paperId) return;
    try {
      await verifyOCRText(paperId, 'model_answer', correctedText);
      setAnswerOCR(prev => prev ? { ...prev, extracted_text: correctedText } : null);
    } catch (error) {
      console.error('Error verifying answer OCR:', error);
      setError('Error updating OCR text. Please try again.');
    }
  };

  const handleVerificationComplete = () => {
    setSuccess(true);
    // Reset form
    setTestTitle('');
    setTestSubject('');
    setTestDescription('');
    setQuestionFile(null);
    setAnswerFile(null);
    setQuestionOCR(null);
    setAnswerOCR(null);
    setPaperId('');
  };

  if (loading) return <Loading />;

  return (
    <div className="max-w-2xl mx-auto">
      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800">Test created and verified successfully!</p>
        </div>
      )}
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4 rounded-t-xl">
          <h2 className="text-lg font-semibold text-white">Create New Test</h2>
        </div>
        
        {/* OCR Status */}
        {loading && (
          <div className="p-4 border-b border-gray-200">
            <OCRStatus status="processing" message="Processing files and extracting text..." />
          </div>
        )}

        {/* OCR Verification UI */}
        {!loading && (questionOCR || answerOCR) && (
          <div className="p-4 border-b border-gray-200 space-y-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Verify Extracted Text</h3>
            
            {questionOCR && (
              <OCRVerification
                fileType="question"
                imagePath={`/files/${questionOCR.file_path}`}
                extractedText={questionOCR.extracted_text}
                confidence={questionOCR.confidence}
                onTextUpdate={handleVerifyQuestion}
                onVerify={handleVerificationComplete}
              />
            )}
            
            {answerOCR && (
              <OCRVerification
                fileType="model_answer"
                imagePath={`/files/${answerOCR.file_path}`}
                extractedText={answerOCR.extracted_text}
                confidence={answerOCR.confidence}
                onTextUpdate={handleVerifyAnswer}
                onVerify={handleVerificationComplete}
              />
            )}
          </div>
        )}
        
        {/* Upload Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Test Title *
            </label>
            <input
              type="text"
              value={testTitle}
              onChange={(e) => setTestTitle(e.target.value)}
              className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter test title"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Subject *
            </label>
            <input
              type="text"
              value={testSubject}
              onChange={(e) => setTestSubject(e.target.value)}
              className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter subject"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={testDescription}
              onChange={(e) => setTestDescription(e.target.value)}
              rows={4}
              className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter test description"
            />
          </div>
          
          <div className="space-y-4">
            <FileUpload
              label="Question Paper *"
              acceptedTypes=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              onFileSelect={setQuestionFile}
              selectedFile={questionFile}
            />
            
            <FileUpload
              label="Model Answer *"
              acceptedTypes=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              onFileSelect={setAnswerFile}
              selectedFile={answerFile}
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm">{error}</div>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium py-3 rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50"
          >
            {loading ? 'Creating Test...' : 'Create Test'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default CreateTest;