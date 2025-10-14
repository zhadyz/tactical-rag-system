import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronRight } from 'lucide-react';
import type { Source } from '../../types';

interface SourceCitationProps {
  source: Source;
  index: number;
}

export const SourceCitation: React.FC<SourceCitationProps> = ({
  source,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatScore = (score: number) => {
    return (score * 100).toFixed(1);
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-3 p-3 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-left"
      >
        <div className="flex-shrink-0">
          {isExpanded ? (
            <ChevronDown size={16} className="text-gray-500" />
          ) : (
            <ChevronRight size={16} className="text-gray-500" />
          )}
        </div>

        <div className="flex-shrink-0">
          <FileText size={16} className="text-primary-600 dark:text-primary-400" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              {source.metadata.source}
            </span>
            {source.metadata.page && (
              <span className="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                Page {source.metadata.page}
              </span>
            )}
          </div>
        </div>

        <div className="flex-shrink-0">
          <span
            className={`text-xs px-2 py-1 rounded-full ${
              source.metadata.score > 0.8
                ? 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400'
                : source.metadata.score > 0.6
                ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
            }`}
          >
            {formatScore(source.metadata.score)}%
          </span>
        </div>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="p-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {source.content}
          </p>
        </div>
      )}
    </div>
  );
};
