import React, { useRef } from 'react';
import { FileUp, X } from 'lucide-react';

interface FileUploadProps {
  label: string;
  acceptedTypes: string;
  onFileSelect: (file: File | null) => void;
  selectedFile: File | null;
}

const FileUpload: React.FC<FileUploadProps> = ({ 
  label, 
  acceptedTypes, 
  onFileSelect, 
  selectedFile 
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    onFileSelect(file);
  };

  const handleRemoveFile = () => {
    onFileSelect(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
      <div
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-400 cursor-pointer transition-colors"
      >
        <FileUp className="h-8 w-8 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-600">Click to upload file</p>
        <p className="text-sm text-gray-400 mt-1">
          {acceptedTypes.replace(/\./g, '').toUpperCase()} files
        </p>
        {selectedFile && (
          <div className="mt-3 flex items-center justify-center space-x-2">
            <p className="text-sm text-indigo-600">Selected: {selectedFile.name}</p>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleRemoveFile();
              }}
              className="text-red-500 hover:text-red-700"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileChange}
        className="hidden"
        accept={acceptedTypes}
      />
    </div>
  );
};

export default FileUpload;