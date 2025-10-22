import React, { useRef, useState, useCallback } from 'react';
import { Upload, X, AlertCircle } from 'lucide-react';
import useStore from '../../store/useStore';
import { api } from '../../services/api';

export const DocumentUpload: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addDocument = useStore((state) => state.addDocument);
  const updateDocument = useStore((state) => state.updateDocument);
  const removeDocument = useStore((state) => state.removeDocument);
  const isUploading = useStore((state) => state.isUploading);
  const setUploading = useStore((state) => state.setUploading);

  // PERFORMANCE OPTIMIZATION: Memoize file handling to prevent recreation on every render
  const handleFile = useCallback(async (file: File) => {
    // Create temporary document entry
    const tempDoc = {
      id: `temp-${Date.now()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date(),
      status: 'uploading' as const,
    };

    try {
      setError(null);
      setUploading(true);

      addDocument(tempDoc);

      // Upload file
      const uploadedDoc = await api.uploadDocument(file);

      // Update with real document info
      updateDocument(tempDoc.id, {
        ...uploadedDoc,
        status: 'ready',
      });
    } catch (err: any) {
      // Remove failed upload from the list
      removeDocument(tempDoc.id);
      setError(err.message || 'Failed to upload document');
      if (import.meta.env.DEV) {
        console.error('Upload error:', err);
      }
    } finally {
      setUploading(false);
    }
  }, [addDocument, updateDocument, removeDocument, setUploading]);

  // PERFORMANCE OPTIMIZATION: Memoize drag handlers
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  }, [handleFile]);

  const handleChooseFile = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleClearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <div className="p-4">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
            : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600'
        }`}
        role="region"
        aria-label="Document upload area"
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleChange}
          accept=".pdf,.txt,.doc,.docx,.md"
          disabled={isUploading}
          aria-label="Choose document file to upload"
          aria-describedby="upload-instructions"
        />

        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center" aria-hidden="true">
            {isUploading ? (
              <div className="animate-spin">
                <Upload size={24} className="text-primary-600" />
              </div>
            ) : (
              <Upload size={24} className="text-gray-400" />
            )}
          </div>

          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1" role="status" aria-live="polite">
              {isUploading ? 'Uploading...' : 'Drop files here or click to upload'}
            </p>
            <p id="upload-instructions" className="text-xs text-gray-500 dark:text-gray-400">
              Supports PDF, TXT, DOC, DOCX, MD
            </p>
          </div>

          <button
            onClick={handleChooseFile}
            disabled={isUploading}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Choose file to upload"
          >
            Choose File
          </button>
        </div>
      </div>

      {error && (
        <div
          className="mt-4 flex items-center gap-2 p-3 bg-error-50 dark:bg-error-900/30 border border-error-200 dark:border-error-800 rounded-lg"
          role="alert"
          aria-live="assertive"
        >
          <AlertCircle size={16} className="text-error-600 dark:text-error-400 flex-shrink-0" aria-hidden="true" />
          <p className="text-sm text-error-700 dark:text-error-300">{error}</p>
          <button
            onClick={handleClearError}
            className="ml-auto text-error-600 dark:text-error-400 hover:text-error-700 dark:hover:text-error-300"
            aria-label="Dismiss error message"
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
};
