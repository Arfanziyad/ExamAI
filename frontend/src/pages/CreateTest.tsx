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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [ocrProcessing, setOcrProcessing] = useState(false);
  const [ocrResults, setOcrResults] = useState<OCRResults | null>(null);
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
    const newId = Date.now().toString();
    const nextQuestionNumber = Math.max(...questionAnswerPairs.map(q => q.main_question_number)) + 1;
    setQuestionAnswerPairs([...questionAnswerPairs, { 
      id: newId, 
      question: '', 
      answer: '', 
      marks: 10,
      question_type: 'subjective',
      question_number: `${nextQuestionNumber}a`,
      main_question_number: nextQuestionNumber,
      sub_question: 'a'
    }]);
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

  const getSubQuestions = (mainQuestionNumber: number) => {
    return questionAnswerPairs.filter(q => 
      q.main_question_number === mainQuestionNumber && q.sub_question
    ).sort((a, b) => (a.sub_question || '').localeCompare(b.sub_question || ''));
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
      formData.append('file', selectedFile);
      formData.append('title', testTitle || 'Untitled Question Paper');
      formData.append('subject', testSubject || 'General');
      formData.append('description', testDescription || '');

      const response = await fetch('http://localhost:5000/api/ocr/process-question-paper-structured', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`OCR processing failed: ${response.status}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error('OCR processing failed');
      }

      // Convert backend format to frontend format
      const questions: QuestionAnswerPair[] = result.questions.map((q: any) => ({
        id: q.display_number || q.question_number.toString(),
        question: q.question_text,
        answer: q.answer_text,
        marks: q.max_marks || 10,
        question_type: q.question_type || 'subjective',
        question_number: q.display_number || q.question_number.toString(),
        main_question_number: q.main_question_number || q.question_number,
        sub_question: q.sub_question || "",
        or_group_id: q.or_group_id
      }));
      
      setOcrResults({ 
        questions,
        or_groups_summary: result.or_groups_summary,
        extracted_text: result.extracted_text,
        confidence: result.confidence
      });

      // Auto-populate the question-answer pairs
      setQuestionAnswerPairs(questions);
      
      // Auto-populate OR groups if detected
      if (result.or_groups_summary?.or_groups?.length > 0) {
        const detectedGroups = result.or_groups_summary.or_groups.map((group: any) => group.group_id);
        setOrGroups(detectedGroups);
        
        // Show notification about auto-detected OR groups
        console.log(`Auto-detected ${detectedGroups.length} OR groups from the scanned document`);
      }

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
                        Extracted and classified {ocrResults.questions.length} question-answer pair(s).
                        Text has been automatically populated in the form fields below.
                        You can review and edit the extracted text as needed.
                      </p>
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
                                  <div key={q.question_number} className="text-xs text-purple-600">
                                    • Question {q.display_number || q.question_number}: {q.question_text.substring(0, 60)}...
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
                        Total Marks: {questionAnswerPairs.reduce((sum, pair) => sum + pair.marks, 0)}
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
                    {orGroups.map(groupId => {
                      const groupQuestions = getQuestionsInGroup(groupId);
                      if (groupQuestions.length === 0) return null;
                      
                      return (
                        <div key={groupId} className="bg-white rounded-lg p-4 mb-3 border border-purple-200">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-purple-900">
                              OR Group {orGroups.indexOf(groupId) + 1}
                            </span>
                            <button
                              type="button"
                              onClick={() => {
                                groupQuestions.forEach(q => removeFromOrGroup(q.id));
                                setOrGroups(orGroups.filter(id => id !== groupId));
                              }}
                              className="text-red-600 hover:text-red-800 text-sm"
                            >
                              Remove Group
                            </button>
                          </div>
                          <div className="text-sm text-purple-600">
                            Questions: {groupQuestions.map((q, idx) => `Q${questionAnswerPairs.findIndex(p => p.id === q.id) + 1}`).join(', ')}
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
                                if (!isNaN(value) && value > 0 && value <= 100) {
                                  updateQuestionAnswerPair(mainQuestion.id, 'marks', value);
                                } else if (e.target.value === '') {
                                  updateQuestionAnswerPair(mainQuestion.id, 'marks', 1);
                                }
                              }}
                              className="w-20 px-2 py-1 border border-gray-300 rounded text-sm focus:border-indigo-500 focus:ring-indigo-500 text-center font-medium"
                              title="Set marks for this question (1-100, decimals allowed)"
                            />
                          </div>
                        </div>
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
                                  if (!isNaN(value) && value > 0 && value <= 100) {
                                    updateQuestionAnswerPair(subQuestion.id, 'marks', value);
                                  } else if (e.target.value === '') {
                                    updateQuestionAnswerPair(subQuestion.id, 'marks', 1);
                                  }
                                }}
                                className="w-16 px-2 py-1 border border-gray-300 rounded text-xs focus:border-indigo-500 focus:ring-indigo-500 text-center font-medium"
                                title="Set marks for this sub-question (1-100, decimals allowed)"
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

  const handleQuestionToggle = (questionId: string) => {
    setSelectedQuestions(prev => 
      prev.includes(questionId)
        ? prev.filter(id => id !== questionId)
        : [...prev, questionId]
    );
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
        <div className="space-y-2">
          {questions.map((question) => {
            const questionIndex = questionAnswerPairs.findIndex(p => p.id === question.id);
            return (
              <label key={question.id} className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-purple-50">
                <input
                  type="checkbox"
                  checked={selectedQuestions.includes(question.id)}
                  onChange={() => handleQuestionToggle(question.id)}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">Question {questionIndex + 1}</span>
                    <span className="text-sm font-semibold text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                      {question.marks} pts
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1 truncate">
                    {question.question.substring(0, 100)}{question.question.length > 100 ? '...' : ''}
                  </p>
                </div>
              </label>
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