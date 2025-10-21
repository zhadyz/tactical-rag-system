import React from 'react';
import { Moon, Sun, Settings, Trash2, Zap } from 'lucide-react';
import useStore from '../../store/useStore';

interface HeaderProps {
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenSettings }) => {
  const darkMode = useStore((state) => state.settings.darkMode);
  const toggleDarkMode = useStore((state) => state.toggleDarkMode);
  const clearChat = useStore((state) => state.clearChat);
  const messageCount = useStore((state) => state.messages.length);

  return (
    <header className="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 backdrop-blur-xl">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Logo and title */}
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow">
            <Zap className="w-6 h-6 text-white" strokeWidth={2.5} fill="currentColor" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
              Tactical RAG
            </h1>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 font-medium">
              Intelligent Document Q&A
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1.5">
          {/* Clear chat button */}
          {messageCount > 0 && (
            <button
              onClick={clearChat}
              className="group p-2.5 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-all duration-150 text-neutral-600 dark:text-neutral-400 hover:text-error-600 dark:hover:text-error-400"
              aria-label="Clear chat"
              title="Clear chat"
            >
              <Trash2 size={20} strokeWidth={2} className="group-hover:scale-110 transition-transform" />
            </button>
          )}

          {/* Dark mode toggle */}
          <button
            onClick={toggleDarkMode}
            className="group p-2.5 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-all duration-150 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100"
            aria-label="Toggle dark mode"
            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {darkMode ? (
              <Sun size={20} strokeWidth={2} className="group-hover:rotate-12 transition-transform" />
            ) : (
              <Moon size={20} strokeWidth={2} className="group-hover:rotate-12 transition-transform" />
            )}
          </button>

          {/* Settings button */}
          <button
            onClick={onOpenSettings}
            className="group p-2.5 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-all duration-150 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100"
            aria-label="Settings"
            title="Settings"
          >
            <Settings size={20} strokeWidth={2} className="group-hover:rotate-45 transition-transform duration-300" />
          </button>
        </div>
      </div>
    </header>
  );
};
