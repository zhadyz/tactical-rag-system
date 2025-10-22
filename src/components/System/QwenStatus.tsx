import React, { useState, useEffect } from 'react';
import { Brain, CheckCircle, XCircle, Download, Loader2, AlertTriangle } from 'lucide-react';
import { getOllamaStatus, verifyQwen, type OllamaStatus } from '../../services/ollamaService';

interface QwenStatusProps {
  autoCheck?: boolean;
  checkInterval?: number;
}

export const QwenStatus: React.FC<QwenStatusProps> = ({
  autoCheck = true,
  checkInterval = 10000,
}) => {
  const [status, setStatus] = useState<OllamaStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check Ollama status
  const checkStatus = async () => {
    try {
      const ollamaStatus = await getOllamaStatus();
      setStatus(ollamaStatus);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check status');
    } finally {
      setLoading(false);
    }
  };

  // Download and verify Qwen model
  const handleDownloadQwen = async () => {
    setDownloading(true);
    setError(null);
    try {
      await verifyQwen();
      await checkStatus(); // Refresh status after download
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download model');
    } finally {
      setDownloading(false);
    }
  };

  // Initial check and periodic updates
  useEffect(() => {
    checkStatus();

    if (autoCheck) {
      const interval = setInterval(checkStatus, checkInterval);
      return () => clearInterval(interval);
    }
  }, [autoCheck, checkInterval]);

  // Determine status indicator
  const getStatusIndicator = () => {
    if (loading) {
      return {
        icon: <Loader2 size={18} className="animate-spin" />,
        color: 'text-neutral-500',
        label: 'Checking...',
      };
    }

    if (error) {
      return {
        icon: <XCircle size={18} />,
        color: 'text-red-500',
        label: 'Error',
      };
    }

    if (!status?.installed) {
      return {
        icon: <XCircle size={18} />,
        color: 'text-red-500',
        label: 'Ollama not installed',
      };
    }

    if (!status?.running) {
      return {
        icon: <AlertTriangle size={18} />,
        color: 'text-yellow-500',
        label: 'Ollama not running',
      };
    }

    if (status?.qwen_available) {
      return {
        icon: <CheckCircle size={18} />,
        color: 'text-green-500',
        label: 'Qwen ready',
      };
    }

    return {
      icon: <AlertTriangle size={18} />,
      color: 'text-yellow-500',
      label: 'Qwen not installed',
    };
  };

  const statusIndicator = getStatusIndicator();

  return (
    <div className="bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Brain size={20} className="text-primary-600 dark:text-primary-400" />
          <h3 className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
            Qwen Model Status
          </h3>
        </div>
        <div className={`flex items-center gap-2 ${statusIndicator.color}`}>
          {statusIndicator.icon}
          <span className="text-xs font-medium">{statusIndicator.label}</span>
        </div>
      </div>

      {/* Status details */}
      <div className="space-y-2 text-sm">
        {status && (
          <>
            <div className="flex justify-between text-neutral-600 dark:text-neutral-400">
              <span>Ollama:</span>
              <span className="font-medium">
                {status.installed ? (status.version || 'Installed') : 'Not installed'}
              </span>
            </div>
            {status.installed && (
              <>
                <div className="flex justify-between text-neutral-600 dark:text-neutral-400">
                  <span>Service:</span>
                  <span className="font-medium">
                    {status.running ? 'Running' : 'Stopped'}
                  </span>
                </div>
                {status.running && (
                  <>
                    <div className="flex justify-between text-neutral-600 dark:text-neutral-400">
                      <span>Models:</span>
                      <span className="font-medium">{status.models.length}</span>
                    </div>
                    <div className="flex justify-between text-neutral-600 dark:text-neutral-400">
                      <span>Recommended:</span>
                      <span className="font-mono text-xs font-medium">
                        {status.recommended_model}
                      </span>
                    </div>
                  </>
                )}
              </>
            )}
          </>
        )}

        {error && (
          <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-700 dark:text-red-400 text-xs">
            {error}
          </div>
        )}

        {/* Action buttons */}
        {status && status.installed && status.running && !status.qwen_available && (
          <div className="mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700">
            <button
              onClick={handleDownloadQwen}
              disabled={downloading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-neutral-400 text-white rounded-lg transition-colors text-sm font-medium"
            >
              {downloading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Downloading Qwen...
                </>
              ) : (
                <>
                  <Download size={16} />
                  Download Qwen Model
                </>
              )}
            </button>
            <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400 text-center">
              This may take several minutes
            </p>
          </div>
        )}

        {/* Installation instructions */}
        {status && !status.installed && (
          <div className="mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700">
            <p className="text-xs text-neutral-600 dark:text-neutral-400">
              Install Ollama from{' '}
              <a
                href="https://ollama.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 dark:text-primary-400 hover:underline"
              >
                ollama.com
              </a>
            </p>
          </div>
        )}

        {status && status.installed && !status.running && (
          <div className="mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700">
            <p className="text-xs text-neutral-600 dark:text-neutral-400">
              Start Ollama service to continue
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
