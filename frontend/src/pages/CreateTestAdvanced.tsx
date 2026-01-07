import React, { useState } from 'react';
import { Upload, FileText, Brain, CheckCircle, Save } from 'lucide-react';
import { processQuestionPaperOCRStructured, createQuestionPaperFromOCR } from '../services/api';

interface ParsedQuestion {
  question_number: number;
  display_number?: string;
  question_text: string;
  answer_text: string;
  max_marks: number;
  question_type: 'subjective' | 'coding';
  main_question_number?: number;
  sub_question?: string;
  or_group_id?: string;
}

interface OCRResult {
  success: boolean;
  extracted_text: string;
  confidence: number;
  questions: ParsedQuestion[];
  metadata: {
    title: string;
    subject: string;
    description: string;
    filename: string;
  };
}

const CreateTestAdvanced: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [questions, setQuestions] = useState<ParsedQuestion[]>([]);
  const [metadata, setMetadata] = useState({
    title: '',
    subject: '',
    description: ''
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setOcrResult(null);
      setQuestions([]);
      setSaveSuccess(false);
    }
  };

  const handleProcessOCR = async () => {
    if (!file) return;

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', metadata.title || 'OCR Question Paper');
      formData.append('subject', metadata.subject || 'General');
      formData.append('description', metadata.description || '');

      const result = await processQuestionPaperOCRStructured(formData);
      setOcrResult(result);
      setQuestions(result.questions);
      
      // Update metadata with OCR result
      setMetadata(prev => ({
        title: prev.title || result.metadata.title,
        subject: prev.subject || result.metadata.subject,
        description: prev.description || result.metadata.description
      }));
    } catch (error) {
      console.error('OCR processing failed:', error);
      alert('Failed to process the image. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleQuestionChange = (index: number, field: keyof ParsedQuestion, value: any) => {
    setQuestions(prev => prev.map((q, i) => 
      i === index ? { ...q, [field]: value } : q
    ));
  };

  const handleSaveQuestionPaper = async () => {
    if (questions.length === 0) return;

    setIsSaving(true);
    try {
      const data = {
        title: metadata.title,
        subject: metadata.subject,
        description: metadata.description,
        questions: questions
      };

      await createQuestionPaperFromOCR(data);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save question paper:', error);
      alert('Failed to save the question paper. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Advanced Test Creation with OCR
        </h1>
        <p className="text-gray-600">
          Upload a question paper image to automatically extract and categorize multiple questions
        </p>
      </div>

      {/* Step 1: Metadata Input */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Test Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Test Title
            </label>
            <input
              type="text"
              value={metadata.title}
              onChange={(e) => setMetadata(prev => ({...prev, title: e.target.value}))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter test title"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Subject
            </label>
            <input
              type="text"
              value={metadata.subject}
              onChange={(e) => setMetadata(prev => ({...prev, subject: e.target.value}))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter subject"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <input
              type="text"
              value={metadata.description}
              onChange={(e) => setMetadata(prev => ({...prev, description: e.target.value}))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter description"
            />
          </div>
        </div>
      </div>

      {/* Step 2: File Upload */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Upload Question Paper</h2>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer text-blue-600 hover:text-blue-500"
          >
            <span className="font-medium">Click to upload</span>
            <span className="text-gray-500"> or drag and drop</span>
          </label>
          <p className="text-sm text-gray-500 mt-2">
            PNG, JPG, GIF up to 10MB
          </p>
          {file && (
            <p className="mt-2 text-sm text-gray-900">
              Selected: {file.name}
            </p>
          )}
        </div>
        
        {file && (
          <button
            onClick={handleProcessOCR}
            disabled={isProcessing}
            className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center"
          >
            {isProcessing ? (
              <>
                <Brain className="animate-spin h-5 w-5 mr-2" />
                Processing OCR...
              </>
            ) : (
              <>
                <FileText className="h-5 w-5 mr-2" />
                Process with OCR
              </>
            )}
          </button>
        )}
      </div>

      {/* Step 3: OCR Results and Question Review */}
      {ocrResult && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">OCR Results</h2>
          
          <div className="mb-4 p-4 bg-gray-50 rounded-md">
            <p className="text-sm text-gray-700">
              <strong>Confidence:</strong> {(ocrResult.confidence * 100).toFixed(1)}%
            </p>
            <p className="text-sm text-gray-700 mt-2">
              <strong>Detected Questions:</strong> {questions.length}
            </p>
          </div>

          {questions.map((question, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium">Question {question.question_number}</h3>
                <div className="flex items-center space-x-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Type
                    </label>
                    <select
                      value={question.question_type}
                      onChange={(e) => handleQuestionChange(index, 'question_type', e.target.value)}
                      className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="subjective">Subjective</option>
                      <option value="coding">Coding</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Marks
                    </label>
                    <input
                      type="number"
                      value={question.max_marks}
                      onChange={(e) => handleQuestionChange(index, 'max_marks', parseInt(e.target.value))}
                      className="w-20 px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="1"
                      max="100"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Question Text
                  </label>
                  <textarea
                    value={question.question_text}
                    onChange={(e) => handleQuestionChange(index, 'question_text', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={4}
                    placeholder="Question text..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model Answer
                  </label>
                  <textarea
                    value={question.answer_text}
                    onChange={(e) => handleQuestionChange(index, 'answer_text', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={4}
                    placeholder="Model answer..."
                  />
                </div>
              </div>
            </div>
          ))}

          {questions.length > 0 && (
            <button
              onClick={handleSaveQuestionPaper}
              disabled={isSaving}
              className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-400 flex items-center justify-center"
            >
              {isSaving ? (
                <>
                  <Brain className="animate-spin h-5 w-5 mr-2" />
                  Saving Question Paper...
                </>
              ) : (
                <>
                  <Save className="h-5 w-5 mr-2" />
                  Save Question Paper
                </>
              )}
            </button>
          )}

          {saveSuccess && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
                <p className="text-green-800">Question paper saved successfully!</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Raw OCR Text (for debugging) */}
      {ocrResult && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Raw OCR Text</h2>
          <div className="bg-gray-50 p-4 rounded-md">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap">
              {ocrResult.extracted_text}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default CreateTestAdvanced;