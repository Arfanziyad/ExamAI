import React, { useState } from 'react';
import { Check, AlertCircle } from 'lucide-react';

interface OCRVerificationProps {
  fileType: 'question' | 'model_answer';
  imagePath?: string;
  extractedText: string;
  confidence: number;
  onTextUpdate: (text: string) => void;
  onVerify: () => void;
}

const OCRVerification: React.FC<OCRVerificationProps> = ({
  fileType,
  imagePath,
  extractedText,
  confidence,
  onTextUpdate,
  onVerify
}) => {
  const [editedText, setEditedText] = useState(extractedText);
  const [isEditing, setIsEditing] = useState(false);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setEditedText(e.target.value);
  };

  const handleSave = () => {
    onTextUpdate(editedText);
    setIsEditing(false);
  };

  const handleVerify = () => {
    onVerify();
    setIsEditing(false);
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            OCR Results - {fileType === 'question' ? 'Question Paper' : 'Model Answer'}
          </h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">Confidence:</span>
            <span className={`font-medium ${getConfidenceColor(confidence)}`}>
              {confidence}%
            </span>
          </div>
        </div>
      </div>

      <div className="p-4">
        {/* Preview and Edit Section */}
        <div className="space-y-4">
          {imagePath && (
            <div className="border rounded-lg overflow-hidden">
              <img
                src={imagePath}
                alt="Document preview"
                className="w-full object-contain max-h-64"
              />
            </div>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700">
                Extracted Text
              </label>
              {confidence < 90 && !isEditing && (
                <div className="flex items-center text-yellow-600 text-sm">
                  <AlertCircle className="h-4 w-4 mr-1" />
                  <span>Review recommended</span>
                </div>
              )}
            </div>

            {isEditing ? (
              <textarea
                value={editedText}
                onChange={handleTextChange}
                rows={6}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="No text extracted"
              />
            ) : (
              <div className="bg-gray-50 rounded-md p-3 text-gray-700 text-sm min-h-[100px]">
                {extractedText || 'No text extracted'}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3">
            {isEditing ? (
              <>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSave}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700"
                >
                  Save Changes
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Edit Text
                </button>
                <button
                  type="button"
                  onClick={handleVerify}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700"
                >
                  <Check className="h-4 w-4 mr-1" />
                  Verify
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OCRVerification;