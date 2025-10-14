import React, { useState, useEffect } from 'react';
import {
  FileText,
  Settings as SettingsIcon,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import useStore from '../../store/useStore';
import { DocumentManagement } from '../Documents/DocumentManagement';
import { api } from '../../services/api';
// Temporarily disable performance imports to debug
// import { usePerformanceStore } from '../../store/performanceStore';
// import { PerformanceMetrics } from '../Performance/PerformanceMetrics';
// import { PerformanceDashboard } from '../Performance/PerformanceDashboard';

export const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showDocManagement, setShowDocManagement] = useState(false);
  // const [showPerfDashboard, setShowPerfDashboard] = useState(false);
  const [documentCount, setDocumentCount] = useState<number | null>(null);
  const settings = useStore((state) => state.settings);
  const updateSettings = useStore((state) => state.updateSettings);

  // Performance metrics - temporarily disabled
  // const latestQuery = usePerformanceStore((state) => state.getLatestQuery());
  // const stats = usePerformanceStore((state) => state.getStats());

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
      className={`border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="flex flex-col h-full">
        {/* Collapse toggle */}
        <div className="flex items-center justify-end p-4 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight size={20} />
            ) : (
              <ChevronLeft size={20} />
            )}
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {!isCollapsed && (
            <>
              {/* Settings Section */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <SettingsIcon size={16} className="text-gray-500" />
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    Settings
                  </h3>
                </div>

                <div className="space-y-3">
                  {/* Mode selector */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Mode
                    </label>
                    <select
                      value={settings.mode}
                      onChange={(e) =>
                        updateSettings({
                          mode: e.target.value as 'simple' | 'adaptive',
                        })
                      }
                      className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                      <option value="simple">Simple</option>
                      <option value="adaptive">Adaptive</option>
                    </select>
                  </div>

                  {/* Use context toggle */}
                  <div className="flex items-center justify-between">
                    <label
                      htmlFor="use-context"
                      className="text-sm text-gray-700 dark:text-gray-300"
                    >
                      Use Context
                    </label>
                    <button
                      id="use-context"
                      onClick={() =>
                        updateSettings({ useContext: !settings.useContext })
                      }
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        settings.useContext
                          ? 'bg-primary-600'
                          : 'bg-gray-200 dark:bg-gray-700'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          settings.useContext ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>

                  {/* Stream response toggle */}
                  <div className="flex items-center justify-between opacity-50 cursor-not-allowed">
                    <label
                      htmlFor="stream-response"
                      className="text-sm text-gray-700 dark:text-gray-300"
                      title="Coming Soon"
                    >
                      Stream Response
                    </label>
                    <button
                      id="stream-response"
                      className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200 dark:bg-gray-700 cursor-not-allowed"
                      disabled
                      title="Coming Soon"
                    >
                      <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-1" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Performance Section - Temporarily disabled for debugging */}
              {/* <div className="mb-6">
                Performance section
              </div> */}

              {/* Documents Section */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <FileText size={16} className="text-gray-500" />
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      Documents
                    </h3>
                  </div>
                  {documentCount !== null && (
                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                      {documentCount}
                    </span>
                  )}
                </div>

                {/* Manage Documents button */}
                <button
                  onClick={() => setShowDocManagement(true)}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-primary-600 hover:bg-primary-700 text-white transition-colors"
                >
                  <FileText size={16} />
                  <span className="text-sm font-medium">Manage Documents</span>
                </button>

                <p className="text-xs text-gray-500 dark:text-gray-400 text-center py-4">
                  Click to view, upload, and manage documents
                </p>
              </div>
            </>
          )}

          {/* Collapsed state icons */}
          {isCollapsed && (
            <div className="flex flex-col items-center gap-4">
              <button
                onClick={() => setShowDocManagement(true)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400"
                title="Manage Documents"
              >
                <FileText size={20} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Document Management Modal */}
      {showDocManagement && (
        <DocumentManagement onClose={() => setShowDocManagement(false)} />
      )}

      {/* Performance Dashboard Modal - Temporarily disabled for debugging */}
      {/* showPerfDashboard && (
        <PerformanceDashboard onClose={() => setShowPerfDashboard(false)} />
      ) */}
    </aside>
  );
};
