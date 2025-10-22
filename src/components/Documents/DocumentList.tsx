import React from 'react';
import { FileText, Trash2, Loader2, CheckCircle, XCircle } from 'lucide-react';
import useStore from '../../store/useStore';
import { api } from '../../services/api';

export const DocumentList: React.FC = () => {
  const documents = useStore((state) => state.documents);
  const removeDocument = useStore((state) => state.removeDocument);

  const handleDelete = async (id: string) => {
    try {
      await api.deleteDocument(id);
      removeDocument(id);
    } catch (err) {
      console.error('Failed to delete document:', err);
      // Optionally show error to user
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <Loader2 size={16} className="text-primary-600 animate-spin" />;
      case 'ready':
        return <CheckCircle size={16} className="text-success-600" />;
      case 'error':
        return <XCircle size={16} className="text-error-600" />;
      default:
        return <FileText size={16} className="text-gray-400" />;
    }
  };

  if (documents.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 dark:to-primary-800/20 rounded-3xl shadow-lg mx-auto mb-6">
          <FileText size={36} className="text-primary-600 dark:text-primary-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          No Documents Yet
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 max-w-sm mx-auto">
          Upload your first document to unlock intelligent Q&A capabilities
        </p>
        <div className="flex items-center justify-center gap-2 text-xs text-gray-500 dark:text-gray-500">
          <FileText size={14} />
          <span>Supports PDF, TXT, DOC, DOCX, MD formats</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="space-y-2">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="card p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div className="flex-shrink-0 w-10 h-10 bg-primary-50 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                <FileText size={20} className="text-primary-600 dark:text-primary-400" />
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {doc.name}
                  </h4>
                  {getStatusIcon(doc.status)}
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                  <span>{formatFileSize(doc.size)}</span>
                  <span>•</span>
                  <span>
                    {new Date(doc.uploadedAt).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <button
                onClick={() => handleDelete(doc.id)}
                disabled={doc.status === 'uploading'}
                className="flex-shrink-0 p-2 rounded-lg hover:bg-error-50 dark:hover:bg-error-900/30 text-gray-400 hover:text-error-600 dark:hover:text-error-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Delete document"
              >
                <Trash2 size={16} />
              </button>
            </div>

            {/* Status message */}
            {doc.status === 'processing' && (
              <div className="mt-2 flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                <Loader2 size={12} className="animate-spin" />
                <span>Processing document...</span>
              </div>
            )}
            {doc.status === 'error' && (
              <div className="mt-2">
                <p className="text-xs font-semibold text-error-600 dark:text-error-400 mb-0.5">
                  Failed to process document
                </p>
                <p className="text-xs text-error-500 dark:text-error-500">
                  Try re-uploading or check the file format
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
