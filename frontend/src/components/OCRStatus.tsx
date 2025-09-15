import React from 'react';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';

interface OCRStatusProps {
  status: 'processing' | 'success' | 'error';
  message?: string;
}

const OCRStatus: React.FC<OCRStatusProps> = ({ status, message }) => {
  const getStatusContent = () => {
    switch (status) {
      case 'processing':
        return {
          icon: <Loader2 className="h-5 w-5 text-indigo-600 animate-spin" />,
          text: message || 'Processing OCR...',
          bgColor: 'bg-indigo-50',
          textColor: 'text-indigo-700'
        };
      case 'success':
        return {
          icon: <CheckCircle className="h-5 w-5 text-green-600" />,
          text: message || 'OCR completed successfully',
          bgColor: 'bg-green-50',
          textColor: 'text-green-700'
        };
      case 'error':
        return {
          icon: <XCircle className="h-5 w-5 text-red-600" />,
          text: message || 'OCR processing failed',
          bgColor: 'bg-red-50',
          textColor: 'text-red-700'
        };
      default:
        return null;
    }
  };

  const content = getStatusContent();
  if (!content) return null;

  return (
    <div className={`${content.bgColor} rounded-lg p-4`}>
      <div className="flex items-center">
        {content.icon}
        <span className={`ml-2 text-sm font-medium ${content.textColor}`}>
          {content.text}
        </span>
      </div>
    </div>
  );
};

export default OCRStatus;