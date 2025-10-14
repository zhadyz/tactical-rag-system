import React from 'react';
import { Zap, Brain } from 'lucide-react';
import useStore from '../../store/useStore';

export const ModeSelector: React.FC = () => {
  const mode = useStore((state) => state.settings.mode);
  const updateSettings = useStore((state) => state.updateSettings);

  const modes = [
    {
      id: 'simple',
      name: 'Simple',
      description: 'Fast, direct answers from documents',
      icon: Zap,
    },
    {
      id: 'adaptive',
      name: 'Adaptive',
      description: 'Intelligent routing with advanced reasoning',
      icon: Brain,
    },
  ] as const;

  return (
    <div className="space-y-3">
      {modes.map((m) => {
        const Icon = m.icon;
        const isSelected = mode === m.id;

        return (
          <button
            key={m.id}
            onClick={() => updateSettings({ mode: m.id })}
            className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
              isSelected
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="flex items-start gap-3">
              <div
                className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
                  isSelected
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                }`}
              >
                <Icon size={20} />
              </div>

              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4
                    className={`font-semibold ${
                      isSelected
                        ? 'text-primary-900 dark:text-primary-100'
                        : 'text-gray-900 dark:text-gray-100'
                    }`}
                  >
                    {m.name}
                  </h4>
                  {isSelected && (
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary-600 flex items-center justify-center">
                      <svg
                        className="w-3 h-3 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={3}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    </span>
                  )}
                </div>
                <p
                  className={`text-sm ${
                    isSelected
                      ? 'text-primary-700 dark:text-primary-300'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {m.description}
                </p>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
};
