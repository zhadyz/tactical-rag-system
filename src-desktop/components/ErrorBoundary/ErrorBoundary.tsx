import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, FileText } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackComponent?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  componentName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState((prevState) => ({
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Log error to file for later analysis (field deployment)
    this.logErrorToFile(error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to console in development
    if (import.meta.env.DEV) {
      console.error('Error Boundary caught an error:', error, errorInfo);
    }
  }

  logErrorToFile = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      const timestamp = new Date().toISOString();
      const componentName = this.props.componentName || 'Unknown';

      const errorLog = {
        timestamp,
        component: componentName,
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
        },
        errorInfo: {
          componentStack: errorInfo.componentStack,
        },
        userAgent: navigator.userAgent,
        url: window.location.href,
      };

      // Store in localStorage as fallback for field deployment
      const existingLogs = localStorage.getItem('error-logs') || '[]';
      const logs = JSON.parse(existingLogs);
      logs.push(errorLog);

      // Keep only last 50 errors
      const trimmedLogs = logs.slice(-50);
      localStorage.setItem('error-logs', JSON.stringify(trimmedLogs));

      // Also store latest error separately for quick access
      localStorage.setItem('latest-error', JSON.stringify(errorLog));
    } catch (err) {
      // Silently fail if logging fails
      console.error('Failed to log error:', err);
    }
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  exportErrorLogs = () => {
    try {
      const logs = localStorage.getItem('error-logs') || '[]';
      const blob = new Blob([logs], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tactical-rag-errors-${new Date().toISOString()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export error logs:', err);
    }
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallbackComponent) {
        return this.props.fallbackComponent;
      }

      const { error, errorCount } = this.state;
      const componentName = this.props.componentName || 'Application';

      return (
        <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-950 p-4">
          <div className="max-w-2xl w-full bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl border border-neutral-200 dark:border-neutral-800 overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-error-500 to-error-600 p-6 text-white">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                  <AlertTriangle size={32} strokeWidth={2} />
                </div>
                <div>
                  <h1 className="text-2xl font-bold mb-1">
                    System Error Detected
                  </h1>
                  <p className="text-error-100 text-sm">
                    {componentName} encountered an unexpected problem
                  </p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* User-friendly message */}
              <div className="bg-neutral-50 dark:bg-neutral-800 rounded-xl p-5 border border-neutral-200 dark:border-neutral-700">
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                  What happened?
                </h2>
                <p className="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed mb-3">
                  The application encountered an error and needs to recover. This error has been logged
                  for technical analysis. You can try the recovery options below.
                </p>
                {errorCount > 1 && (
                  <div className="mt-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                    <p className="text-sm text-amber-800 dark:text-amber-200 font-medium">
                      This error has occurred {errorCount} times. If it persists, a full reload may be required.
                    </p>
                  </div>
                )}
              </div>

              {/* Error details (collapsible in production) */}
              {error && (
                <details className="bg-neutral-50 dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 overflow-hidden">
                  <summary className="px-5 py-3 cursor-pointer text-sm font-semibold text-neutral-900 dark:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors">
                    Technical Details (for support)
                  </summary>
                  <div className="px-5 pb-4 pt-2 space-y-3">
                    <div>
                      <p className="text-xs font-semibold text-neutral-500 dark:text-neutral-400 mb-1">
                        Error Message:
                      </p>
                      <p className="text-xs text-neutral-700 dark:text-neutral-300 font-mono bg-neutral-100 dark:bg-neutral-900 p-2 rounded">
                        {error.toString()}
                      </p>
                    </div>
                    {error.stack && (
                      <div>
                        <p className="text-xs font-semibold text-neutral-500 dark:text-neutral-400 mb-1">
                          Stack Trace:
                        </p>
                        <pre className="text-xs text-neutral-700 dark:text-neutral-300 font-mono bg-neutral-100 dark:bg-neutral-900 p-2 rounded overflow-x-auto max-h-32 overflow-y-auto">
                          {error.stack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              )}

              {/* Recovery actions */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                  Recovery Options
                </h3>

                <div className="grid grid-cols-1 gap-3">
                  {/* Try again */}
                  <button
                    onClick={this.handleReset}
                    className="flex items-center gap-3 p-4 bg-primary-600 hover:bg-primary-700 text-white rounded-xl transition-colors text-left group"
                  >
                    <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                      <RefreshCw size={20} strokeWidth={2} />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-sm">Try Again</p>
                      <p className="text-xs text-primary-100">Attempt to recover without reloading</p>
                    </div>
                  </button>

                  {/* Reload page */}
                  <button
                    onClick={this.handleReload}
                    className="flex items-center gap-3 p-4 bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-900 dark:text-neutral-100 rounded-xl transition-colors text-left group"
                  >
                    <div className="w-10 h-10 bg-neutral-200 dark:bg-neutral-700 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                      <RefreshCw size={20} strokeWidth={2} />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-sm">Reload Page</p>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400">
                        Full page reload (recommended if error persists)
                      </p>
                    </div>
                  </button>

                  {/* Go home */}
                  <button
                    onClick={this.handleGoHome}
                    className="flex items-center gap-3 p-4 bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-900 dark:text-neutral-100 rounded-xl transition-colors text-left group"
                  >
                    <div className="w-10 h-10 bg-neutral-200 dark:bg-neutral-700 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Home size={20} strokeWidth={2} />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-sm">Return to Home</p>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400">
                        Navigate back to the main page
                      </p>
                    </div>
                  </button>

                  {/* Export logs */}
                  <button
                    onClick={this.exportErrorLogs}
                    className="flex items-center gap-3 p-4 bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-900 dark:text-neutral-100 rounded-xl transition-colors text-left group"
                  >
                    <div className="w-10 h-10 bg-neutral-200 dark:bg-neutral-700 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                      <FileText size={20} strokeWidth={2} />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-sm">Export Error Logs</p>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400">
                        Download logs for technical support
                      </p>
                    </div>
                  </button>
                </div>
              </div>

              {/* Field support instructions */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">
                  For Field Operators
                </h4>
                <ul className="text-xs text-blue-800 dark:text-blue-300 space-y-1 list-disc list-inside">
                  <li>Error details have been saved to local storage</li>
                  <li>Try "Reload Page" first, then "Try Again" if that fails</li>
                  <li>Export error logs and share with technical support if issue persists</li>
                  <li>Check system resources (memory, disk space) if errors continue</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
