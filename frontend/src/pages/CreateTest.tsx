import React, { useState } from 'react';
import Loading from '../components/Loading';
import { Upload, Camera, FileText, Loader2, Plus, Trash2, Edit3 } from 'lucide-react';

interface QuestionAnswerPair {
  id: string;
  question: string;
  answer: string;
  marks: number;
  question_type: string;  // "subjective" or "coding-python"
}

const CreateTest = () => {
  const [testTitle, setTestTitle] = useState('');
  const [testSubject, setTestSubject] = useState('');
  const [testDescription, setTestDescription] = useState('');
  const [questionAnswerPairs, setQuestionAnswerPairs] = useState<QuestionAnswerPair[]>([
    { id: '1', question: '', answer: '', marks: 10, question_type: 'subjective' }
  ]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  
  // OCR-related state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [ocrProcessing, setOcrProcessing] = useState(false);
  const [ocrResults, setOcrResults] = useState<{questions: QuestionAnswerPair[]} | null>(null);
  const [showManualEntry, setShowManualEntry] = useState(true);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    // Validate basic info
    if (!testTitle || !testSubject) {
      setError('Please fill in test title and subject');
      return;
    }

    // Validate questions and answers
    const validPairs = questionAnswerPairs.filter(pair => 
      pair.question.trim() !== '' && pair.answer.trim() !== ''
    );

    if (validPairs.length === 0) {
      setError('Please add at least one question with an answer');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        title: testTitle,
        subject: testSubject,
        description: testDescription,
        questions: validPairs.map((pair, index) => ({
          question_text: pair.question,
          answer_text: pair.answer,
          question_number: index + 1,
          max_marks: pair.marks,
          question_type: pair.question_type
        }))
      };

      const response = await fetch('http://localhost:5000/api/question-papers/multiple', {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: {
          'Content-Type': 'application/json',
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

  // Question-Answer pair management functions
  const addQuestionAnswerPair = () => {
    const newId = (questionAnswerPairs.length + 1).toString();
    setQuestionAnswerPairs([...questionAnswerPairs, { 
      id: newId, 
      question: '', 
      answer: '', 
      marks: 10,
      question_type: 'subjective'
    }]);
  };

  const removeQuestionAnswerPair = (id: string) => {
    if (questionAnswerPairs.length > 1) {
      setQuestionAnswerPairs(questionAnswerPairs.filter(pair => pair.id !== id));
    }
  };

  const updateQuestionAnswerPair = (id: string, field: keyof QuestionAnswerPair, value: string | number) => {
    setQuestionAnswerPairs(questionAnswerPairs.map(pair => 
      pair.id === id ? { ...pair, [field]: value } : pair
    ));
  };

  // OCR functions
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      
      // Create preview URL
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      
      // Reset any previous OCR results
      setOcrResults(null);
    }
  };

  const processOCR = async () => {
    if (!selectedFile) {
      setError('Please select an image file first');
      return;
    }

    setOcrProcessing(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);

      const response = await fetch('http://localhost:5000/api/ocr/process-question-paper', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`OCR processing failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Parse the extracted text into multiple questions and answers
      const questions = parseOCRResults(result.question_text || '', result.answer_text || '');
      
      setOcrResults({ questions });

      // Auto-populate the question-answer pairs
      setQuestionAnswerPairs(questions);
      
    } catch (error) {
      console.error('OCR error:', error);
      setError(`OCR processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setOcrProcessing(false);
    }
  };

  // Parse OCR results into multiple question-answer pairs
  const parseOCRResults = (questionText: string, answerText: string): QuestionAnswerPair[] => {
    // Split questions and answers by common patterns
    const questionLines = questionText.split(/\n(?=\d+[\.\)]|\b[Qq]uestion|\b[Qq]\.)/);
    const answerLines = answerText.split(/\n(?=\d+[\.\)]|\b[Aa]nswer|\b[Aa]ns\.)/);
    
    const pairs: QuestionAnswerPair[] = [];
    const maxCount = Math.max(questionLines.length, answerLines.length);
    
    for (let i = 0; i < maxCount; i++) {
      const question = questionLines[i] || '';
      const answer = answerLines[i] || '';
      
      if (question.trim() || answer.trim()) {
        pairs.push({
          id: (i + 1).toString(),
          question: question.trim(),
          answer: answer.trim(),
          marks: 10,
          question_type: 'subjective'
        });
      }
    }
    
    // If no clear separation was found, create a single pair
    if (pairs.length === 0) {
      pairs.push({
        id: '1',
        question: questionText.trim(),
        answer: answerText.trim(),
        marks: 10,
        question_type: 'subjective'
      });
    }
    
    return pairs;
  };

  const clearOCR = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setOcrResults(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
  };

  const handleReset = () => {
    setTestTitle('');
    setTestSubject('');
    setTestDescription('');
    setQuestionAnswerPairs([{ id: '1', question: '', answer: '', marks: 10, question_type: 'subjective' }]);
    setSuccess(false);
    setError('');
    clearOCR();
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

        {/* OCR Section */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 bg-gray-50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <Camera className="h-5 w-5 mr-2 text-indigo-600" />
              Upload Question Paper (OCR)
            </h3>
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => setShowManualEntry(!showManualEntry)}
                className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                {showManualEntry ? 'Hide Manual Entry' : 'Show Manual Entry'}
              </button>
            </div>
          </div>
          
          <p className="text-gray-600 mb-4">
            Upload an image containing both questions and model answers. Our OCR will automatically extract and classify the text.
          </p>

          <div className="space-y-4">
            {/* File Upload */}
            <div>
              <input
                type="file"
                id="image-upload"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              <label
                htmlFor="image-upload"
                className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-white hover:bg-gray-50"
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className="w-8 h-8 mb-2 text-gray-400" />
                  <p className="mb-2 text-sm text-gray-500">
                    <span className="font-semibold">Click to upload</span> an image
                  </p>
                  <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB</p>
                </div>
              </label>
            </div>

            {/* Preview and Process */}
            {selectedFile && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Selected: {selectedFile.name}</span>
                  <button
                    type="button"
                    onClick={clearOCR}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>
                
                {previewUrl && (
                  <div className="max-w-md">
                    <img 
                      src={previewUrl} 
                      alt="Preview" 
                      className="w-full h-auto rounded-lg shadow-md"
                    />
                  </div>
                )}

                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={processOCR}
                    disabled={ocrProcessing}
                    className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {ocrProcessing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Processing OCR...
                      </>
                    ) : (
                      <>
                        <FileText className="h-4 w-4 mr-2" />
                        Process OCR
                      </>
                    )}
                  </button>
                </div>

                {/* OCR Results */}
                {ocrResults && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <FileText className="h-5 w-5 text-green-600 mr-2" />
                      <span className="font-medium text-green-800">OCR Processing Complete!</span>
                    </div>
                    <p className="text-sm text-green-700">
                      Extracted and classified {ocrResults.questions.length} question-answer pair(s).
                      Text has been automatically populated in the form fields below.
                      You can review and edit the extracted text as needed.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Questions and Answers */}
        {showManualEntry && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <Edit3 className="h-5 w-5 mr-2 text-indigo-600" />
                  Questions and Model Answers
                </h3>
                <div className="bg-indigo-50 px-3 py-1 rounded-lg">
                  <span className="text-sm font-medium text-indigo-700">
                    Total Marks: {questionAnswerPairs.reduce((sum, pair) => sum + pair.marks, 0)}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={addQuestionAnswerPair}
                className="flex items-center px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Question
              </button>
            </div>

            <div className="space-y-6">
              {questionAnswerPairs.map((pair, index) => (
                <div key={pair.id} className="border border-gray-200 rounded-lg p-6 bg-gray-50">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-md font-medium text-gray-800">
                      Question {index + 1}
                    </h4>
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        <label className="text-sm text-gray-600">Type:</label>
                        <select
                          value={pair.question_type}
                          onChange={(e) => updateQuestionAnswerPair(pair.id, 'question_type', e.target.value)}
                          className="px-3 py-1 border border-gray-300 rounded text-sm focus:border-indigo-500 focus:ring-indigo-500"
                        >
                          <option value="subjective">Subjective</option>
                          <option value="coding-python">Coding - Python</option>
                        </select>
                      </div>
                      <div className="flex items-center space-x-2">
                        <label className="text-sm text-gray-600">Marks:</label>
                        <input
                          type="number"
                          min="1"
                          max="100"
                          value={pair.marks}
                          onChange={(e) => updateQuestionAnswerPair(pair.id, 'marks', parseInt(e.target.value) || 10)}
                          className="w-16 px-2 py-1 border border-gray-300 rounded text-sm focus:border-indigo-500 focus:ring-indigo-500"
                        />
                      </div>
                      {questionAnswerPairs.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeQuestionAnswerPair(pair.id)}
                          className="text-red-600 hover:text-red-800 p-1"
                          title="Remove question"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Question Input */}
                    <div>
                      <label className="block">
                        <span className="text-gray-700 text-sm font-medium">
                          Question Text {pair.question_type === 'coding-python' && <span className="text-indigo-600">(Python Coding)</span>}
                        </span>
                        <textarea
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                          rows={6}
                          placeholder={
                            pair.question_type === 'coding-python' 
                              ? `Write a Python function to solve the following problem:\n\nExample: "Write a function that takes a list of numbers and returns the sum of even numbers."`
                              : `Enter question ${index + 1} here...`
                          }
                          value={pair.question}
                          onChange={(e) => updateQuestionAnswerPair(pair.id, 'question', e.target.value)}
                          required
                        />
                      </label>
                    </div>

                    {/* Answer Input */}
                    <div>
                      <label className="block">
                        <span className="text-gray-700 text-sm font-medium">
                          Model Answer {pair.question_type === 'coding-python' && <span className="text-indigo-600">(Python Code)</span>}
                        </span>
                        <textarea
                          className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 ${
                            pair.question_type === 'coding-python' ? 'font-mono text-sm' : ''
                          }`}
                          rows={6}
                          placeholder={
                            pair.question_type === 'coding-python'
                              ? `def solve_problem(numbers):\n    return sum(num for num in numbers if num % 2 == 0)\n\n# Test cases:\n# test: [1,2,3,4,5,6] -> 12`
                              : `Enter model answer for question ${index + 1}...`
                          }
                          value={pair.answer}
                          onChange={(e) => updateQuestionAnswerPair(pair.id, 'answer', e.target.value)}
                          required
                        />
                      </label>
                      {pair.question_type === 'coding-python' && (
                        <p className="mt-1 text-xs text-gray-500">
                          💡 Tip: Include test cases in comments (e.g., # test: input -&gt; expected_output)
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

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