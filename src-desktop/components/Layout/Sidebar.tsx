import React, { useState, useEffect } from 'react';
import {
  FileText,
  ChevronLeft,
  ChevronRight,
  BarChart3,
} from 'lucide-react';
import { DocumentManagement } from '../Documents/DocumentManagement';
import { PerformanceDashboard } from '../Performance/PerformanceDashboard';
import { api } from '../../services/api';

export const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showDocManagement, setShowDocManagement] = useState(false);
  const [showPerfDashboard, setShowPerfDashboard] = useState(false);
  const [documentCount, setDocumentCount] = useState<number | null>(null);

  // Fetch document count on mount
  useEffect(() => {
    const fetchDocumentCount = async () => {
      try {
        const data = await api.listDocuments();
        setDocumentCount(data.total_documents);
      } catch (error) {
        console.error('Failed to fetch document count:', error);
      }
    };
    fetchDocumentCount();
  }, []);

  return (
    <aside
      className={`border-r border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-72'
      }`}
    >
      <div className="flex flex-col h-full">
        {/* Collapse toggle */}
        <div className="flex items-center justify-end p-4 border-b border-neutral-200 dark:border-neutral-800">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="group p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-all duration-150 text-neutral-600 dark:text-neutral-400"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight size={20} strokeWidth={2} className="group-hover:translate-x-0.5 transition-transform" />
            ) : (
              <ChevronLeft size={20} strokeWidth={2} className="group-hover:translate-x-[-2px] transition-transform" />
            )}
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {!isCollapsed && (
            <>
              {/* Documents Section */}
              <div className="space-y-4">
                <div className="flex items-center justify-between px-1">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                      <FileText size={16} className="text-primary-600 dark:text-primary-400" strokeWidth={2} />
                    </div>
                    <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                      Documents
                    </h3>
                  </div>
                  {documentCount !== null && (
                    <span className="inline-flex items-center justify-center min-w-[24px] h-6 px-2 text-xs font-bold text-primary-700 dark:text-primary-400 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                      {documentCount}
                    </span>
                  )}
                </div>

                {/* Manage Documents button */}
                <button
                  onClick={() => setShowDocManagement(true)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-b from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white transition-all duration-150 shadow-sm hover:shadow-md active:scale-[0.98] group"
                >
                  <FileText size={18} strokeWidth={2} />
                  <span className="text-sm font-semibold">Manage Documents</span>
                </button>

                <p className="text-xs text-neutral-500 dark:text-neutral-400 text-center leading-relaxed">
                  View, upload, and manage your document library
                </p>
              </div>

              <div className="divider"></div>

              {/* Performance Section */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 px-1">
                  <div className="w-8 h-8 bg-neutral-100 dark:bg-neutral-800 rounded-lg flex items-center justify-center">
                    <BarChart3 size={16} className="text-neutral-600 dark:text-neutral-400" strokeWidth={2} />
                  </div>
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                    Performance
                  </h3>
                </div>

                {/* Performance Dashboard button */}
                <button
                  onClick={() => setShowPerfDashboard(true)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-900 dark:text-neutral-100 transition-all duration-150 active:scale-[0.98] group"
                >
                  <BarChart3 size={18} strokeWidth={2} />
                  <span className="text-sm font-semibold">View Metrics</span>
                </button>

                <p className="text-xs text-neutral-500 dark:text-neutral-400 text-center leading-relaxed">
                  Detailed performance analytics and timing history
                </p>
              </div>
            </>
          )}

          {/* Collapsed state icons */}
          {isCollapsed && (
            <div className="flex flex-col items-center gap-3">
              <button
                onClick={() => setShowDocManagement(true)}
                className="group p-3 rounded-xl hover:bg-primary-100 dark:hover:bg-primary-900/30 transition-all duration-150 text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400"
                title="Manage Documents"
              >
                <FileText size={22} strokeWidth={2} className="group-hover:scale-110 transition-transform" />
              </button>
              <button
                onClick={() => setShowPerfDashboard(true)}
                className="group p-3 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-all duration-150 text-neutral-600 dark:text-neutral-400"
                title="Performance Metrics"
              >
                <BarChart3 size={22} strokeWidth={2} className="group-hover:scale-110 transition-transform" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Document Management Modal */}
      {showDocManagement && (
        <DocumentManagement onClose={() => setShowDocManagement(false)} />
      )}

      {/* Performance Dashboard Modal */}
      {showPerfDashboard && (
        <PerformanceDashboard onClose={() => setShowPerfDashboard(false)} />
      )}
    </aside>
  );
};
