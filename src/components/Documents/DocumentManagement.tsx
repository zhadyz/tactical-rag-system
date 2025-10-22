import React, { useState, useEffect, useRef } from 'react';
import { FileText, Upload, RefreshCw, X, AlertCircle, CheckCircle, Database } from 'lucide-react';
import { api } from '../../services/api';
import type { DocumentListResponse, ReindexResponse } from '../../types';

export const DocumentManagement: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [documents, setDocuments] = useState<DocumentListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await api.listDocuments();
      setDocuments(data);
      setError(null);
    } catch (err: any) {
      setError(`Failed to load documents: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleFileUpload = async (file: File) => {
    try {
      setUploading(true);
      setError(null);
      setSuccess(null);

      await api.uploadDocument(file);
      setSuccess(`File "${file.name}" uploaded successfully. Click "Reindex" to process it.`);

      // Don't reload documents yet - wait for reindex
    } catch (err: any) {
      setError(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleReindex = async () => {
    try {
      setReindexing(true);
      setError(null);
      setSuccess(null);

      const result: ReindexResponse = await api.reindexDocuments();
      setSuccess(
        `Reindexing complete! Processed ${result.total_files} files into ${result.total_chunks} chunks in ${result.processing_time_seconds.toFixed(1)}s`
      );

      // Reload documents after reindex
      await loadDocuments();
    } catch (err: any) {
      setError(`Reindexing failed: ${err.message}`);
    } finally {
      setReindexing(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden border border-gray-200 dark:border-gray-700 pointer-events-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
              <Database className="text-primary-600 dark:text-primary-400" size={24} />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Document Management
              </h2>
              {documents && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {documents.total_documents} documents · {documents.total_chunks} chunks
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto" style={{ maxHeight: 'calc(90vh - 180px)' }}>
          {/* Error/Success messages */}
          {error && (
            <div className="m-6 flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg shadow-sm">
              <AlertCircle size={20} className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-red-900 dark:text-red-200 mb-1">
                  Operation Failed
                </p>
                <p className="text-sm text-red-700 dark:text-red-300 mb-2">{error}</p>
                <p className="text-xs text-red-600 dark:text-red-400">
                  Suggested action: Try again or check if the backend service is running.
                </p>
              </div>
              <button onClick={() => setError(null)} className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 transition-colors">
                <X size={16} />
              </button>
            </div>
          )}

          {success && (
            <div className="m-6 flex items-start gap-3 p-4 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg">
              <CheckCircle size={20} className="text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-green-700 dark:text-green-300">{success}</p>
              </div>
              <button onClick={() => setSuccess(null)} className="text-green-600 dark:text-green-400">
                <X size={16} />
              </button>
            </div>
          )}

          {/* Upload Section */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Upload New Document
            </h3>
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={handleFileSelect}
                accept=".pdf,.txt,.doc,.docx,.md"
                disabled={uploading}
              />

              <div className="flex flex-col items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                  {uploading ? (
                    <div className="animate-spin">
                      <Upload size={24} className="text-primary-600" />
                    </div>
                  ) : (
                    <Upload size={24} className="text-gray-400" />
                  )}
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
                    {uploading ? 'Uploading...' : 'Drop files here or click to upload'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Supports PDF, TXT, DOC, DOCX, MD
                  </p>
                </div>

                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Choose File
                </button>
              </div>
            </div>
          </div>

          {/* Documents List */}
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Indexed Documents
              </h3>
              <button
                onClick={handleReindex}
                disabled={reindexing || loading}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium transition-colors"
              >
                <RefreshCw size={16} className={reindexing ? 'animate-spin' : ''} />
                {reindexing ? 'Reindexing...' : 'Reindex All'}
              </button>
            </div>

            {loading ? (
              // Loading skeleton
              <div className="animate-pulse space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 bg-gray-300 dark:bg-gray-700 rounded-lg" />
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-3/4" />
                        <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded w-1/2" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : documents && documents.documents.length > 0 ? (
              <div className="space-y-3">
                {documents.documents.map((doc) => (
                  <div
                    key={doc.file_hash}
                    className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 transition-colors bg-gray-50 dark:bg-gray-900/50"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                        <FileText size={20} className="text-primary-600 dark:text-primary-400" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
                          {doc.file_name}
                        </h4>
                        <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                          <span>{formatFileSize(doc.file_size_bytes)}</span>
                          <span>•</span>
                          <span>{doc.num_chunks} chunks</span>
                          <span>•</span>
                          <span>
                            {new Date(doc.processing_date).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              // Enhanced empty state
              <div className="text-center py-12 px-4">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 dark:to-primary-800/20 rounded-3xl shadow-lg mb-6">
                  <FileText size={36} className="text-primary-600 dark:text-primary-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  No Documents Yet
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-6 max-w-sm mx-auto">
                  Upload your first document to start building your knowledge base. Then click "Reindex All" to process it.
                </p>
                <div className="flex items-center justify-center gap-2 text-xs text-gray-500 dark:text-gray-500">
                  <Upload size={14} />
                  <span>Drag and drop or click "Choose File" above</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 rounded-lg text-sm font-medium transition-colors"
          >
            Close
          </button>
        </div>
        </div>
      </div>
    </>
  );
};
