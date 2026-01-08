import React, { useState } from 'react';
import Loading from '../components/Loading';
import { Upload, Camera, FileText, Loader2, Plus, Trash2, Edit3 } from 'lucide-react';

interface QuestionAnswerPair {
  id: string;
  question: string;
  answer: string;
  marks: number;  // Supports decimal values (e.g., 2.5, 10.5)
  question_type: string;  // "subjective" or "coding-python"
  // Sub-question support (e.g., "1", "2a", "3b")
  question_number: string;
  main_question_number: number;
  sub_question?: string;  // "a", "b", "c", etc.
  // OR Groups Support
  or_group_id?: string;
}

interface ORGroupSummary {
  group_id: string;
  title: string;
  questions: any[];
  total_marks: number;
}

interface OCRResults {
  questions: QuestionAnswerPair[];
  or_groups_summary?: {
    or_groups: ORGroupSummary[];
    standalone_questions: any[];
    total_or_groups: number;
    auto_detected: boolean;
  };
  extracted_text?: string;
  confidence?: number;
}

const CreateTest = () => {
  const [testTitle, setTestTitle] = useState('');
  const [testSubject, setTestSubject] = useState('');
  const [testDescription, setTestDescription] = useState('');
  const [questionAnswerPairs, setQuestionAnswerPairs] = useState<QuestionAnswerPair[]>([
    { 
      id: '1', 
      question: '', 
      answer: '', 
      marks: 10, 
      question_type: 'subjective',
      question_number: '1a',
      main_question_number: 1,
      sub_question: 'a'
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  
  // OR Groups state
  const [orGroups, setOrGroups] = useState<string[]>([]);
  const [showOrGroupConfig, setShowOrGroupConfig] = useState(false);
  
  // OCR-related state
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [ocrProcessing, setOcrProcessing] = useState(false);
  const [ocrProcessingProgress, setOcrProcessingProgress] = useState({ current: 0, total: 0 });
  const [ocrResults, setOcrResults] = useState<OCRResults | null>(null);
  const [showManualEntry, setShowManualEntry] = useState(true);
  
  // Add Question Modal state
  const [showAddQuestionModal, setShowAddQuestionModal] = useState(false);
  const [newQuestion, setNewQuestion] = useState({ question: '', answer: '', marks: 10, question_type: 'subjective' });

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
          question_type: pair.question_type,
          // OR Groups Support
          or_group_id: pair.or_group_id,
          // Sub-question support  
          main_question_number: pair.main_question_number,
          sub_question: pair.sub_question
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
    setShowAddQuestionModal(true);
  };

  const handleAddQuestionConfirm = () => {
    if (!newQuestion.question.trim() || !newQuestion.answer.trim()) {
      setError('Please fill in both question and answer');
      return;
    }
    
    const newId = Date.now().toString();
    const nextQuestionNumber = Math.max(...questionAnswerPairs.map(q => q.main_question_number)) + 1;
    setQuestionAnswerPairs([...questionAnswerPairs, { 
      id: newId, 
      question: newQuestion.question, 
      answer: newQuestion.answer, 
      marks: newQuestion.marks,
      question_type: newQuestion.question_type,
      question_number: `${nextQuestionNumber}a`,
      main_question_number: nextQuestionNumber,
      sub_question: 'a'
    }]);
    
    // Reset and close modal
    setNewQuestion({ question: '', answer: '', marks: 10, question_type: 'subjective' });
    setShowAddQuestionModal(false);
    setError('');
  };

  const handleCancelAddQuestion = () => {
    setNewQuestion({ question: '', answer: '', marks: 10, question_type: 'subjective' });
    setShowAddQuestionModal(false);
    setError('');
  };

  const addSubQuestion = (mainQuestionNumber: number) => {
    const newId = Date.now().toString();
    // Find existing sub-questions for this main question
    const existingSubs = questionAnswerPairs.filter(q => 
      q.main_question_number === mainQuestionNumber && q.sub_question
    );
    
    // Determine next sub-question letter
    const usedLetters = existingSubs.map(q => q.sub_question).filter(Boolean);
    const nextLetter = String.fromCharCode(97 + usedLetters.length); // 'a', 'b', 'c', etc.
    
    setQuestionAnswerPairs([...questionAnswerPairs, {
      id: newId,
      question: '',
      answer: '',
      marks: 10,
      question_type: 'subjective',
      question_number: `${mainQuestionNumber}${nextLetter}`,
      main_question_number: mainQuestionNumber,
      sub_question: nextLetter
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

  // OR Groups helper functions
  const createOrGroup = (questionIds: string[]) => {
    const groupId = `group_${Date.now()}`;
    
    setQuestionAnswerPairs(questionAnswerPairs.map(pair => {
      if (questionIds.includes(pair.id)) {
        return {
          ...pair,
          or_group_id: groupId
        };
      }
      return pair;
    }));
    
    setOrGroups([...orGroups, groupId]);
  };

  const removeFromOrGroup = (questionId: string) => {
    setQuestionAnswerPairs(questionAnswerPairs.map(pair => 
      pair.id === questionId 
        ? { ...pair, or_group_id: undefined }
        : pair
    ));
  };

  const getQuestionsInGroup = (groupId: string) => {
    return questionAnswerPairs.filter(q => q.or_group_id === groupId);
  };

  const getUngrouppedQuestions = () => {
    return questionAnswerPairs.filter(q => !q.or_group_id);
  };

  // Helper functions for sub-question management
  const getMainQuestions = () => {
    return questionAnswerPairs.filter(q => !q.sub_question);
  };

  // Check if a main question has sub-questions (for marks display logic)
  const hasSubQuestions = (mainQuestionNumber: number) => {
    return questionAnswerPairs.some(q => 
      q.main_question_number === mainQuestionNumber && q.sub_question
    );
  };

  // Calculate total marks (only count questions that should have marks)
  const calculateTotalMarks = () => {
    return questionAnswerPairs.reduce((sum, pair) => {
      // Only count marks if:
      // 1. It's a sub-question (always has marks), OR
      // 2. It's a main question without sub-questions (standalone)
      if (pair.sub_question || !hasSubQuestions(pair.main_question_number)) {
        return sum + pair.marks;
      }
      return sum;
    }, 0);
  };

  const getSubQuestions = (mainQuestionNumber: number) => {
    return questionAnswerPairs.filter(q => 
      q.main_question_number === mainQuestionNumber && q.sub_question
    ).sort((a, b) => (a.sub_question || '').localeCompare(b.sub_question || ''));
  };

  // OCR functions
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setSelectedFiles(files);
      
      // Create preview URLs for all files
      const urls = files.map(file => URL.createObjectURL(file));
      setPreviewUrls(urls);
      
      // Reset any previous OCR results
      setOcrResults(null);
    }
  };

  const processOCR = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one image file first');
      return;
    }

    setOcrProcessing(true);
    setError('');
    setOcrProcessingProgress({ current: 0, total: selectedFiles.length });

    try {
      let allQuestions: QuestionAnswerPair[] = [];
      let allOrGroups: string[] = [];
      let combinedConfidence = 0;
      let questionIdCounter = 1;

      // Process each file sequentially
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        setOcrProcessingProgress({ current: i + 1, total: selectedFiles.length });

        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', testTitle || 'Untitled Question Paper');
        formData.append('subject', testSubject || 'General');
        formData.append('description', testDescription || '');

        const response = await fetch('http://localhost:5000/api/ocr/process-question-paper-structured', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`OCR processing failed for ${file.name}: ${response.status}`);
        }

        const result = await response.json();
        
        if (!result.success) {
          throw new Error(`OCR processing failed for ${file.name}`);
        }

        // Convert backend format to frontend format and adjust IDs
        const questions: QuestionAnswerPair[] = result.questions.map((q: any) => {
          const questionId = `page${i + 1}-${questionIdCounter++}`;
          return {
            id: questionId,
            question: q.question_text,
            answer: q.answer_text,
            marks: q.max_marks || 10,
            question_type: q.question_type || 'subjective',
            question_number: q.display_number || q.question_number.toString(),
            main_question_number: q.main_question_number || q.question_number,
            sub_question: q.sub_question || "",
            or_group_id: q.or_group_id ? `page${i + 1}-${q.or_group_id}` : undefined
          };
        });

        allQuestions = [...allQuestions, ...questions];
        combinedConfidence += result.confidence || 0;

        // Collect OR groups with page prefix
        if (result.or_groups_summary?.or_groups?.length > 0) {
          const pageGroups = result.or_groups_summary.or_groups.map((group: any) => `page${i + 1}-${group.group_id}`);
          allOrGroups = [...allOrGroups, ...pageGroups];
        }
      }

      // Calculate average confidence
      const avgConfidence = combinedConfidence / selectedFiles.length;

      setOcrResults({ 
        questions: allQuestions,
        or_groups_summary: allOrGroups.length > 0 ? {
          or_groups: allOrGroups.map((gid, idx) => ({
            group_id: gid,
            title: `OR Group ${idx + 1}`,
            questions: allQuestions.filter(q => q.or_group_id === gid),
            total_marks: allQuestions.filter(q => q.or_group_id === gid).reduce((sum, q) => sum + q.marks, 0)
          })),
          standalone_questions: allQuestions.filter(q => !q.or_group_id),
          total_or_groups: allOrGroups.length,
          auto_detected: true
        } : undefined,
        extracted_text: `Combined from ${selectedFiles.length} page(s)`,
        confidence: avgConfidence
      });

      // Auto-populate the question-answer pairs
      setQuestionAnswerPairs(allQuestions);
      
      // Auto-populate OR groups if detected
      if (allOrGroups.length > 0) {
        setOrGroups(allOrGroups);
        console.log(`Auto-detected ${allOrGroups.length} OR groups from ${selectedFiles.length} scanned page(s)`);
      }

    } catch (error) {
      console.error('OCR error:', error);
      setError(`OCR processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setOcrProcessing(false);
      setOcrProcessingProgress({ current: 0, total: 0 });
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
    setSelectedFiles([]);
    previewUrls.forEach(url => URL.revokeObjectURL(url));
    setPreviewUrls([]);
    setOcrResults(null);
    setOcrProcessingProgress({ current: 0, total: 0 });
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
            Upload one or more images containing questions and model answers. Select multiple pages to scan an entire exam paper. Our OCR will automatically extract and classify the text.
          </p>

          <div className="space-y-4">
            {/* File Upload */}
            <div>
              <input
                type="file"
                id="image-upload"
                accept="image/*"
                multiple
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
                    <span className="font-semibold">Click to upload</span> one or more images
                  </p>
                  <p className="text-xs text-gray-500">Select multiple pages for complete exam papers • PNG, JPG, GIF up to 10MB each</p>
                </div>
              </label>
            </div>

            {/* Preview and Process */}
            {selectedFiles.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    Selected: {selectedFiles.length} page{selectedFiles.length > 1 ? 's' : ''} ({selectedFiles.map(f => f.name).join(', ')})
                  </span>
                  <button
                    type="button"
                    onClick={clearOCR}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove All
                  </button>
                </div>
                
                {previewUrls.length > 0 && (
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                    {previewUrls.map((url, index) => (
                      <div key={index} className="relative">
                        <div className="absolute top-2 left-2 bg-indigo-600 text-white text-xs px-2 py-1 rounded-full font-semibold z-10">
                          Page {index + 1}
                        </div>
                        <img 
                          src={url} 
                          alt={`Preview ${index + 1}`} 
                          className="w-full h-auto rounded-lg shadow-md border-2 border-gray-200"
                        />
                      </div>
                    ))}
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
                        Processing Page {ocrProcessingProgress.current} of {ocrProcessingProgress.total}...
                      </>
                    ) : (
                      <>
                        <Camera className="h-4 w-4 mr-2" />
                        Process {selectedFiles.length} Page{selectedFiles.length > 1 ? 's' : ''}
                      </>
                    )}
                  </button>
                </div>

                {/* OCR Results */}
                {ocrResults && (
                  <div className="space-y-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center mb-2">
                        <FileText className="h-5 w-5 text-green-600 mr-2" />
                        <span className="font-medium text-green-800">OCR Processing Complete!</span>
                        {ocrResults.confidence && (
                          <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                            {Math.round(ocrResults.confidence * 100)}% confidence
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-green-700">
                        Extracted and classified {ocrResults.questions.length} question-answer pair(s) from {selectedFiles.length} page{selectedFiles.length > 1 ? 's' : ''}.
                        Text has been automatically populated in the form fields below.
                        You can review and edit the extracted text as needed.
                      </p>
                    </div>

                    {/* Detailed OCR Results Review */}
                    <div className="bg-white border border-gray-300 rounded-lg p-4">
                      <div className="flex items-center mb-3">
                        <FileText className="h-5 w-5 text-indigo-600 mr-2" />
                        <span className="font-medium text-indigo-800">Review Extracted Questions & Answers</span>
                      </div>
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {ocrResults.questions.map((q, index) => (
                          <div key={q.id} className="bg-gray-50 border border-gray-200 rounded-md p-3">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-semibold text-indigo-700">
                                Question {q.question_number}
                              </span>
                              <div className="flex items-center space-x-2">
                                <div className="flex items-center space-x-1">
                                  <label className="text-xs font-medium text-gray-600">Marks:</label>
                                  <input
                                    type="number"
                                    min="1"
                                    max="100"
                                    step="0.5"
                                    value={q.marks}
                                    onChange={(e) => {
                                      const value = parseFloat(e.target.value);
                                      if (!isNaN(value) && value >= 1 && value <= 100) {
                                        // Update marks in both ocrResults and questionAnswerPairs
                                        const updatedQuestions = ocrResults.questions.map(question => 
                                          question.id === q.id ? { ...question, marks: value } : question
                                        );
                                        setOcrResults({ ...ocrResults, questions: updatedQuestions });
                                        
                                        const updatedPairs = questionAnswerPairs.map(pair =>
                                          pair.id === q.id ? { ...pair, marks: value } : pair
                                        );
                                        setQuestionAnswerPairs(updatedPairs);
                                      }
                                    }}
                                    className="w-16 px-2 py-1 border border-indigo-300 rounded text-xs focus:border-indigo-500 focus:ring-indigo-500 text-center font-semibold bg-white"
                                    title="Edit marks for this question"
                                  />
                                </div>
                                <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                                  {q.question_type === 'coding-python' ? 'Coding' : 'Subjective'}
                                </span>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <div>
                                <p className="text-xs font-medium text-gray-600 mb-1">Question:</p>
                                <p className="text-sm text-gray-800 bg-white p-2 rounded border border-gray-200">
                                  {q.question || '(No question text extracted)'}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs font-medium text-gray-600 mb-1">Model Answer:</p>
                                <p className="text-sm text-gray-800 bg-white p-2 rounded border border-gray-200">
                                  {q.answer || '(No answer text extracted)'}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs text-gray-600">
                          💡 All extracted content has been auto-filled in the form below. Scroll down to review and edit each question.
                        </p>
                      </div>
                    </div>

                    {/* OR Groups Auto-Detection Results */}
                    {ocrResults.or_groups_summary?.auto_detected && (
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                        <div className="flex items-center mb-3">
                          <Edit3 className="h-5 w-5 text-purple-600 mr-2" />
                          <span className="font-medium text-purple-800">
                            OR Groups Auto-Detected! 🎯
                          </span>
                        </div>
                        
                        <div className="space-y-3">
                          <p className="text-sm text-purple-700">
                            Found {ocrResults.or_groups_summary.total_or_groups} OR group(s) in the scanned document.
                            Students can choose from these alternative questions:
                          </p>
                          
                          {ocrResults.or_groups_summary.or_groups.map((group, index) => (
                            <div key={group.group_id} className="bg-white rounded-md p-3 border border-purple-200">
                              <div className="text-sm font-medium text-purple-800 mb-2">
                                OR Group {index + 1} ({group.total_marks} marks total)
                              </div>
                              <div className="space-y-1">
                                {group.questions.map((q: any) => (
                                  <div key={q.id || q.question_number} className="text-xs text-purple-600">
                                    • Question {q.question_number}: {q.question ? q.question.substring(0, 60) : 'No text'}...
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                          
                          <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mt-3">
                            <p className="text-xs text-blue-700">
                              💡 <strong>Review & Edit:</strong> OR groups have been automatically configured below. 
                              You can manually adjust groupings using the "Configure OR Groups" button if needed.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Add Question Modal */}
        {showAddQuestionModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-gray-900">Add New Question</h3>
                  <button
                    onClick={handleCancelAddQuestion}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="space-y-4">
                  {/* Question Type and Marks */}
                  <div className="flex items-center space-x-4">
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Question Type</label>
                      <select
                        value={newQuestion.question_type}
                        onChange={(e) => setNewQuestion({ ...newQuestion, question_type: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:border-indigo-500 focus:ring-indigo-500"
                      >
                        <option value="subjective">Subjective</option>
                        <option value="coding-python">Coding - Python</option>
                      </select>
                    </div>
                    <div className="w-32">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Marks</label>
                      <input
                        type="number"
                        min="1"
                        max="100"
                        step="0.5"
                        value={newQuestion.marks}
                        onChange={(e) => {
                          const value = parseFloat(e.target.value);
                          if (!isNaN(value) && value >= 1 && value <= 100) {
                            setNewQuestion({ ...newQuestion, marks: value });
                          }
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:border-indigo-500 focus:ring-indigo-500"
                      />
                    </div>
                  </div>

                  {/* Question Input Box */}
                  <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Question Text {newQuestion.question_type === 'coding-python' && <span className="text-indigo-600">(Python Coding)</span>}
                    </label>
                    <textarea
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:border-indigo-500 focus:ring-indigo-500"
                      rows={6}
                      placeholder={
                        newQuestion.question_type === 'coding-python'
                          ? 'Write a Python function to solve the following problem...'
                          : 'Enter your question here...'
                      }
                      value={newQuestion.question}
                      onChange={(e) => setNewQuestion({ ...newQuestion, question: e.target.value })}
                    />
                  </div>

                  {/* Answer Input Box */}
                  <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Model Answer {newQuestion.question_type === 'coding-python' && <span className="text-indigo-600">(Python Code)</span>}
                    </label>
                    <textarea
                      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:border-indigo-500 focus:ring-indigo-500 ${
                        newQuestion.question_type === 'coding-python' ? 'font-mono text-sm' : ''
                      }`}
                      rows={6}
                      placeholder={
                        newQuestion.question_type === 'coding-python'
                          ? 'def solve_problem():\n    # Your solution here\n    pass'
                          : 'Enter the model answer here...'
                      }
                      value={newQuestion.answer}
                      onChange={(e) => setNewQuestion({ ...newQuestion, answer: e.target.value })}
                    />
                    {newQuestion.question_type === 'coding-python' && (
                      <p className="mt-2 text-xs text-gray-500">
                        💡 Tip: Include test cases in comments (e.g., # test: input -&gt; expected_output)
                      </p>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={handleCancelAddQuestion}
                      className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleAddQuestionConfirm}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      Add Question
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Questions and Answers */}
        {showManualEntry && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <Edit3 className="h-5 w-5 mr-2 text-indigo-600" />
                  Questions and Model Answers
                </h3>
                <div className="bg-indigo-50 px-4 py-2 rounded-lg border border-indigo-200">
                  <div className="flex items-center space-x-4">
                    <div>
                      <span className="text-sm font-medium text-indigo-700">
                        Total Marks: {calculateTotalMarks()}
                      </span>
                    </div>
                    <div className="text-xs text-indigo-600">
                      {questionAnswerPairs.length} question{questionAnswerPairs.length !== 1 ? 's' : ''}
                    </div>
                    {questionAnswerPairs.some(q => q.or_group_id) && (
                      <div className="text-xs text-purple-600 font-medium">
                        📋 OR Groups: {new Set(questionAnswerPairs.filter(q => q.or_group_id).map(q => q.or_group_id)).size}
                      </div>
                    )}
                  </div>
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
              <button
                type="button"
                onClick={() => setShowOrGroupConfig(!showOrGroupConfig)}
                className="flex items-center px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
              >
                <Edit3 className="h-4 w-4 mr-1" />
                Configure OR Groups
              </button>
            </div>

            {/* OR Groups Configuration */}
            {showOrGroupConfig && (
              <div className="border-2 border-purple-200 rounded-lg p-6 bg-purple-50">
                <h4 className="text-lg font-medium text-purple-900 mb-4">OR Groups Configuration</h4>
                <p className="text-sm text-purple-700 mb-4">
                  Create groups where students must answer EITHER one question OR another (e.g., "Answer Question 1 OR Question 2").
                </p>
                
                {/* Existing OR Groups */}
                {orGroups.length > 0 && (
                  <div className="mb-6">
                    <h5 className="font-medium text-purple-800 mb-3">Existing OR Groups:</h5>
                    <p className="text-xs text-purple-600 mb-3 italic">
                      Students can choose to answer any ONE question from each OR group
                    </p>
                    {orGroups.map(groupId => {
                      const groupQuestions = getQuestionsInGroup(groupId);
                      if (groupQuestions.length === 0) return null;
                      
                      return (
                        <div key={groupId} className="bg-white rounded-lg p-4 mb-3 border-2 border-purple-300 shadow-sm">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-2">
                              <span className="font-semibold text-purple-900 text-base">
                                OR Group {orGroups.indexOf(groupId) + 1}
                              </span>
                              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                                Choose 1 of {groupQuestions.length}
                              </span>
                            </div>
                            <button
                              type="button"
                              onClick={() => {
                                groupQuestions.forEach(q => removeFromOrGroup(q.id));
                                setOrGroups(orGroups.filter(id => id !== groupId));
                              }}
                              className="text-red-600 hover:text-red-800 text-sm font-medium"
                            >
                              Remove Group
                            </button>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {groupQuestions.map((q, idx) => (
                              <div key={q.id} className="flex items-center">
                                <span className="bg-purple-100 text-purple-800 px-3 py-1.5 rounded-lg font-medium text-sm border border-purple-200">
                                  {q.question_number}
                                </span>
                                {idx < groupQuestions.length - 1 && (
                                  <span className="mx-2 text-purple-500 font-bold">OR</span>
                                )}
                              </div>
                            ))}
                          </div>
                          <div className="mt-2 text-xs text-gray-600">
                            Total marks: {groupQuestions.reduce((sum, q) => sum + q.marks, 0)} pts
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
                
                {/* Create New OR Group */}
                <ORGroupCreator 
                  questions={getUngrouppedQuestions()}
                  questionAnswerPairs={questionAnswerPairs}
                  onCreateGroup={createOrGroup}
                />
              </div>
            )}

            <div className="space-y-6">
              {getMainQuestions().map((mainQuestion) => (
                <div key={`main-${mainQuestion.id}`} className="space-y-4">
                  {/* Main Question */}
                  <div className={`border rounded-lg p-6 ${mainQuestion.or_group_id ? 'border-purple-300 bg-purple-50' : 'border-gray-200 bg-gray-50'}`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <h4 className="text-md font-medium text-gray-800">
                          Question {mainQuestion.question_number}
                        </h4>
                        {mainQuestion.or_group_id && (
                          <div className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-medium">
                            OR Group
                          </div>
                        )}
                        <button
                          type="button"
                          onClick={() => addSubQuestion(mainQuestion.main_question_number)}
                          className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded hover:bg-blue-200"
                          title="Add sub-question (a, b, c...)"
                        >
                          + Sub-question
                        </button>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center space-x-2">
                          <label className="text-sm text-gray-600">Type:</label>
                          <select
                            value={mainQuestion.question_type}
                            onChange={(e) => updateQuestionAnswerPair(mainQuestion.id, 'question_type', e.target.value)}
                            className="px-3 py-1 border border-gray-300 rounded text-sm focus:border-indigo-500 focus:ring-indigo-500"
                          >
                            <option value="subjective">Subjective</option>
                            <option value="coding-python">Coding - Python</option>
                          </select>
                        </div>
                        {/* Only show marks for standalone questions (no sub-questions) */}
                        {!hasSubQuestions(mainQuestion.main_question_number) && (
                          <div className="flex items-center space-x-2">
                            <label className="text-sm text-gray-600 font-medium">Marks:</label>
                            <div className="flex items-center space-x-1">
                              <input
                                type="number"
                                min="1"
                                max="100"
                                step="0.5"
                                value={mainQuestion.marks}
                                onChange={(e) => {
                                  const value = parseFloat(e.target.value);
                                  if (!isNaN(value) && value >= 1 && value <= 100) {
                                    updateQuestionAnswerPair(mainQuestion.id, 'marks', value);
                                  } else if (e.target.value === '') {
                                    updateQuestionAnswerPair(mainQuestion.id, 'marks', 1);
                                  }
                                }}
                                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm focus:border-indigo-500 focus:ring-indigo-500 text-center font-medium"
                                title="Set marks for this question (minimum 1)"
                              />
                            </div>
                          </div>
                        )}
                        {/* Show label for parent questions */}
                        {hasSubQuestions(mainQuestion.main_question_number) && (
                          <div className="text-xs text-gray-500 bg-gray-100 px-3 py-1 rounded">
                            Parent question (marks set in sub-questions)
                          </div>
                        )}
                        {questionAnswerPairs.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeQuestionAnswerPair(mainQuestion.id)}
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
                            Question Text {mainQuestion.question_type === 'coding-python' && <span className="text-indigo-600">(Python Coding)</span>}
                          </span>
                          <textarea
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            rows={6}
                            placeholder={
                              mainQuestion.question_type === 'coding-python' 
                                ? `Write a Python function to solve the following problem:\n\nExample: "Write a function that takes a list of numbers and returns the sum of even numbers."`
                                : `Enter question ${mainQuestion.question_number} here...`
                            }
                            value={mainQuestion.question}
                            onChange={(e) => updateQuestionAnswerPair(mainQuestion.id, 'question', e.target.value)}
                            required
                          />
                        </label>
                      </div>

                      {/* Answer Input */}
                      <div>
                        <label className="block">
                          <span className="text-gray-700 text-sm font-medium">
                            Model Answer {mainQuestion.question_type === 'coding-python' && <span className="text-indigo-600">(Python Code)</span>}
                          </span>
                          <textarea
                            className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 ${
                              mainQuestion.question_type === 'coding-python' ? 'font-mono text-sm' : ''
                            }`}
                            rows={6}
                            placeholder={
                              mainQuestion.question_type === 'coding-python'
                                ? `def solve_problem(numbers):\n    return sum(num for num in numbers if num % 2 == 0)\n\n# Test cases:\n# test: [1,2,3,4,5,6] -> 12`
                                : `Enter model answer for question ${mainQuestion.question_number}...`
                            }
                            value={mainQuestion.answer}
                            onChange={(e) => updateQuestionAnswerPair(mainQuestion.id, 'answer', e.target.value)}
                            required
                          />
                        </label>
                        {mainQuestion.question_type === 'coding-python' && (
                          <p className="mt-1 text-xs text-gray-500">
                            💡 Tip: Include test cases in comments (e.g., # test: input -&gt; expected_output)
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Sub-questions */}
                  {getSubQuestions(mainQuestion.main_question_number).map((subQuestion) => (
                    <div key={`sub-${subQuestion.id}`} className="ml-6 border-l-4 border-blue-200 pl-4">
                      <div className={`border rounded-lg p-4 ${subQuestion.or_group_id ? 'border-purple-200 bg-purple-25' : 'border-gray-100 bg-white'}`}>
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <h5 className="text-sm font-medium text-gray-700">
                              Question {subQuestion.question_number}
                            </h5>
                            {subQuestion.or_group_id && (
                              <div className="bg-purple-100 text-purple-700 px-2 py-1 rounded-full text-xs font-medium">
                                OR Group
                              </div>
                            )}
                          </div>
                          <div className="flex items-center space-x-3">
                            <div className="flex items-center space-x-2">
                              <label className="text-sm text-gray-600">Type:</label>
                              <select
                                value={subQuestion.question_type}
                                onChange={(e) => updateQuestionAnswerPair(subQuestion.id, 'question_type', e.target.value)}
                                className="px-2 py-1 border border-gray-300 rounded text-xs focus:border-indigo-500 focus:ring-indigo-500"
                              >
                                <option value="subjective">Subjective</option>
                                <option value="coding-python">Coding - Python</option>
                              </select>
                            </div>
                            <div className="flex items-center space-x-2">
                              <label className="text-sm text-gray-600 font-medium">Marks:</label>
                              <input
                                type="number"
                                min="1"
                                max="100"
                                step="0.5"
                                value={subQuestion.marks}
                                onChange={(e) => {
                                  const value = parseFloat(e.target.value);
                                  if (!isNaN(value) && value >= 1 && value <= 100) {
                                    updateQuestionAnswerPair(subQuestion.id, 'marks', value);
                                  } else if (e.target.value === '') {
                                    updateQuestionAnswerPair(subQuestion.id, 'marks', 1);
                                  }
                                }}
                                className="w-16 px-2 py-1 border border-gray-300 rounded text-xs focus:border-indigo-500 focus:ring-indigo-500 text-center font-medium"
                                title="Set marks for this sub-question (minimum 1)"
                              />
                            </div>
                            <button
                              type="button"
                              onClick={() => removeQuestionAnswerPair(subQuestion.id)}
                              className="text-red-500 hover:text-red-700 p-1"
                              title="Remove sub-question"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                          {/* Sub-question Input */}
                          <div>
                            <label className="block">
                              <span className="text-gray-600 text-sm font-medium">
                                Sub-question Text
                              </span>
                              <textarea
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                rows={4}
                                placeholder={`Enter sub-question ${subQuestion.question_number} here...`}
                                value={subQuestion.question}
                                onChange={(e) => updateQuestionAnswerPair(subQuestion.id, 'question', e.target.value)}
                                required
                              />
                            </label>
                          </div>

                          {/* Sub-answer Input */}
                          <div>
                            <label className="block">
                              <span className="text-gray-600 text-sm font-medium">
                                Model Answer
                              </span>
                              <textarea
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                rows={4}
                                placeholder={`Enter model answer for ${subQuestion.question_number}...`}
                                value={subQuestion.answer}
                                onChange={(e) => updateQuestionAnswerPair(subQuestion.id, 'answer', e.target.value)}
                                required
                              />
                            </label>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
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

// OR Group Creator Component
interface ORGroupCreatorProps {
  questions: QuestionAnswerPair[];
  questionAnswerPairs: QuestionAnswerPair[];
  onCreateGroup: (questionIds: string[]) => void;
}

const ORGroupCreator: React.FC<ORGroupCreatorProps> = ({ questions, questionAnswerPairs, onCreateGroup }) => {
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);

  // Group questions by main question number for better OR group visualization
  const groupedQuestions = questions.reduce((groups, question) => {
    const mainNum = question.main_question_number;
    if (!groups[mainNum]) {
      groups[mainNum] = [];
    }
    groups[mainNum].push(question);
    return groups;
  }, {} as Record<number, QuestionAnswerPair[]>);

  const handleQuestionToggle = (questionId: string) => {
    setSelectedQuestions(prev => 
      prev.includes(questionId)
        ? prev.filter(id => id !== questionId)
        : [...prev, questionId]
    );
  };

  const handleGroupToggle = (groupQuestions: QuestionAnswerPair[]) => {
    const groupIds = groupQuestions.map(q => q.id);
    const allSelected = groupIds.every(id => selectedQuestions.includes(id));
    
    if (allSelected) {
      setSelectedQuestions(prev => prev.filter(id => !groupIds.includes(id)));
    } else {
      setSelectedQuestions(prev => [...new Set([...prev, ...groupIds])]);
    }
  };

  const handleCreateGroup = () => {
    if (selectedQuestions.length >= 2) {
      onCreateGroup(selectedQuestions);
      setSelectedQuestions([]);
    }
  };

  if (questions.length < 2) {
    return (
      <div className="text-center py-4 text-purple-600">
        <p>Add at least 2 questions to create OR groups.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">


      <div>
        <label className="block text-sm font-medium text-purple-700 mb-2">
          Select Questions for OR Group (minimum 2)
        </label>
        <p className="text-xs text-purple-600 mb-3 italic">
          Students will choose ONE from this group. Example: "1a and 1b" OR "2"
        </p>
        <div className="space-y-3">
          {Object.entries(groupedQuestions).map(([mainNum, groupQuestions]) => {
            const hasMultiple = groupQuestions.length > 1;
            const allSelected = groupQuestions.every(q => selectedQuestions.includes(q.id));
            const someSelected = groupQuestions.some(q => selectedQuestions.includes(q.id));
            const totalMarks = groupQuestions.reduce((sum, q) => sum + q.marks, 0);
            
            return (
              <div key={mainNum} className="border-2 rounded-lg transition-colors border-gray-300 hover:border-purple-300">
                {hasMultiple ? (
                  <div>
                    {/* Group header for sub-questions */}
                    <div 
                      className="flex items-center space-x-3 p-3 bg-purple-50 cursor-pointer hover:bg-purple-100 rounded-t-lg"
                      onClick={() => handleGroupToggle(groupQuestions)}
                    >
                      <input
                        type="checkbox"
                        checked={allSelected}
                        onChange={() => handleGroupToggle(groupQuestions)}
                        className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        onClick={(e) => e.stopPropagation()}
                      />
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-purple-900">
                            Q{mainNum} Group ({groupQuestions.map(q => q.sub_question).join(', ')})
                          </span>
                          <span className="text-sm font-semibold text-indigo-600 bg-indigo-100 px-2 py-1 rounded">
                            {totalMarks} pts total
                          </span>
                          <span className="text-xs text-purple-600">
                            {groupQuestions.length} sub-questions
                          </span>
                        </div>
                      </div>
                    </div>
                    {/* Sub-questions */}
                    <div className="bg-white">
                      {groupQuestions.map((question, idx) => (
                        <label 
                          key={question.id} 
                          className={`flex items-center space-x-3 p-3 pl-10 cursor-pointer hover:bg-purple-50 transition-colors ${
                            idx === groupQuestions.length - 1 ? 'rounded-b-lg' : 'border-b border-gray-200'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={selectedQuestions.includes(question.id)}
                            onChange={() => handleQuestionToggle(question.id)}
                            className="h-3 w-3 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                          />
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-semibold text-purple-800 text-sm">
                                {question.question_number}
                              </span>
                              <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                                {question.marks} pts
                              </span>
                              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                                {question.question_type === 'coding-python' ? 'Coding' : 'Subjective'}
                              </span>
                            </div>
                            <p className="text-xs text-gray-600 mt-1 truncate">
                              {question.question.substring(0, 80)}{question.question.length > 80 ? '...' : ''}
                            </p>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                ) : (
                  /* Standalone question */
                  <label className="flex items-center space-x-3 p-3 hover:bg-purple-50 cursor-pointer transition-colors rounded-lg">
                    <input
                      type="checkbox"
                      checked={selectedQuestions.includes(groupQuestions[0].id)}
                      onChange={() => handleQuestionToggle(groupQuestions[0].id)}
                      className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-purple-900 bg-purple-100 px-2 py-1 rounded">
                          {groupQuestions[0].question_number}
                        </span>
                        <span className="text-sm font-semibold text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                          {groupQuestions[0].marks} pts
                        </span>
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                          {groupQuestions[0].question_type === 'coding-python' ? 'Coding' : 'Subjective'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1 truncate">
                        {groupQuestions[0].question.substring(0, 100)}{groupQuestions[0].question.length > 100 ? '...' : ''}
                      </p>
                    </div>
                  </label>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <button
        type="button"
        onClick={handleCreateGroup}
        disabled={selectedQuestions.length < 2}
        className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Create OR Group ({selectedQuestions.length} questions selected
        {selectedQuestions.length > 0 && (
          <span className="ml-1">
            - {selectedQuestions.reduce((sum, id) => {
              const question = questions.find(q => q.id === id);
              return sum + (question?.marks || 0);
            }, 0)} total marks
          </span>
        )})
      </button>
    </div>
  );
};

export default CreateTest;