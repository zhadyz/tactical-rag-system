import React from 'react';
import { X, BarChart3, Trash2 } from 'lucide-react';
import { TimingHistory } from './TimingHistory';
import { ErrorBoundary } from '../ErrorBoundary/ErrorBoundary';
import { usePerformanceStore } from '../../store/performanceStore';

interface PerformanceDashboardProps {
  onClose: () => void;
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({ onClose }) => {
  const clearHistory = usePerformanceStore((state) => state.clearHistory);
  const stats = usePerformanceStore((state) => state.stats);

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear performance history?')) {
      clearHistory();
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col pointer-events-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-neutral-200 dark:border-neutral-700">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
                <BarChart3 className="text-primary-600 dark:text-primary-400" size={20} />
              </div>
              <div>
                <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
                  Performance Dashboard
                </h2>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  Detailed query performance metrics and history
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {stats.totalQueries > 0 && (
                <button
                  onClick={handleClearHistory}
                  className="p-2 text-neutral-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  title="Clear History"
                >
                  <Trash2 size={18} />
                </button>
              )}
              <button
                onClick={onClose}
                className="p-2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {stats.totalQueries === 0 ? (
              // Empty state when no queries yet
              <div className="h-full flex items-center justify-center">
                <div className="text-center max-w-md mx-auto space-y-6">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 dark:to-primary-800/20 rounded-3xl shadow-lg">
                    <BarChart3 size={36} className="text-primary-600 dark:text-primary-400" />
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
                      No Performance Data Yet
                    </h3>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed">
                      Start asking questions to see detailed performance metrics, timing insights, and cache effectiveness.
                    </p>
                  </div>
                  <div className="pt-4">
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-100 dark:bg-neutral-800 rounded-lg text-xs text-neutral-600 dark:text-neutral-400">
                      <BarChart3 size={14} />
                      <span>Performance tracking starts automatically</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <ErrorBoundary componentName="TimingHistory">
                <TimingHistory limit={20} showChart={true} />
              </ErrorBoundary>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-neutral-200 dark:border-neutral-700 p-4 bg-neutral-50 dark:bg-neutral-800">
            <p className="text-xs text-center text-neutral-500 dark:text-neutral-400">
              Performance data is stored locally and persists across sessions
            </p>
          </div>
        </div>
      </div>
    </>
  );
};
