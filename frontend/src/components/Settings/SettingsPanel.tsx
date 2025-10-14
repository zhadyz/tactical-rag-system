import React from 'react';
import { X } from 'lucide-react';
import { ModeSelector } from './ModeSelector';
import useStore from '../../store/useStore';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  isOpen,
  onClose,
}) => {
  const settings = useStore((state) => state.settings);
  const updateSettings = useStore((state) => state.updateSettings);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 bottom-0 w-96 bg-white dark:bg-gray-800 shadow-2xl z-50 overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Settings
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400"
              aria-label="Close settings"
            >
              <X size={20} />
            </button>
          </div>

          {/* Settings sections */}
          <div className="space-y-6">
            {/* Query Mode */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Query Mode
              </h3>
              <ModeSelector />
            </div>

            {/* Query Options */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Query Options
              </h3>
              <div className="space-y-4">
                {/* Use Context */}
                <div className="flex items-center justify-between">
                  <div>
                    <label
                      htmlFor="use-context-panel"
                      className="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                      Use Context
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Include conversation history in queries
                    </p>
                  </div>
                  <button
                    id="use-context-panel"
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

                {/* Stream Response */}
                <div className="flex items-center justify-between">
                  <div>
                    <label
                      htmlFor="stream-response-panel"
                      className="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                      Stream Response
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Stream responses in real-time for faster perceived latency
                    </p>
                  </div>
                  <button
                    id="stream-response-panel"
                    onClick={() =>
                      updateSettings({ streamResponse: !settings.streamResponse })
                    }
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.streamResponse
                        ? 'bg-primary-600'
                        : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.streamResponse ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>

            {/* About */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                About
              </h3>
              <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                  <strong>Tactical RAG</strong>
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Version 3.5.0
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  Intelligent document Q&A powered by advanced retrieval and
                  reasoning techniques.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
