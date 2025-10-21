import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronRight, BookOpen } from 'lucide-react';
import type { Source } from '../../types';

interface SourceCitationProps {
  source: Source;
  index: number;
}

export const SourceCitation: React.FC<SourceCitationProps> = ({
  source,
  index,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatScore = (score: number) => {
    return (score * 100).toFixed(1);
  };

  // Determine relevance badge styling based on score
  const getRelevanceBadge = (score: number) => {
    if (score > 0.8) {
      return {
        color: 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400 border-success-200 dark:border-success-800/50',
        label: 'High relevance',
      };
    } else if (score > 0.6) {
      return {
        color: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400 border-warning-200 dark:border-warning-800/50',
        label: 'Medium relevance',
      };
    } else {
      return {
        color: 'bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-400 border-neutral-200 dark:border-neutral-700',
        label: 'Lower relevance',
      };
    }
  };

  const relevanceBadge = getRelevanceBadge(source.metadata.score);

  return (
    <div className="group/citation border border-neutral-200 dark:border-neutral-800 rounded-xl overflow-hidden
                    transition-all duration-200 hover:border-neutral-300 dark:hover:border-neutral-700
                    hover:shadow-md bg-white dark:bg-neutral-900">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-3 p-4 hover:bg-neutral-50/50 dark:hover:bg-neutral-800/50
                   transition-all duration-150 text-left group/button"
      >
        {/* Expand icon */}
        <div className="flex-shrink-0 transition-transform duration-200 group-hover/button:scale-110">
          {isExpanded ? (
            <ChevronDown size={18} className="text-neutral-500 dark:text-neutral-400" />
          ) : (
            <ChevronRight size={18} className="text-neutral-500 dark:text-neutral-400" />
          )}
        </div>

        {/* File icon */}
        <div className="flex-shrink-0 w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-lg
                        flex items-center justify-center transition-all duration-200
                        group-hover/button:bg-primary-200 dark:group-hover/button:bg-primary-900/50
                        group-hover/button:scale-105">
          <FileText size={16} className="text-primary-600 dark:text-primary-400" strokeWidth={2} />
        </div>

        {/* File info */}
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 truncate
                           group-hover/button:text-primary-700 dark:group-hover/button:text-primary-400
                           transition-colors duration-150">
              {source.metadata.source}
            </span>
          </div>
          {source.metadata.page && (
            <div className="flex items-center gap-1.5 text-xs text-neutral-500 dark:text-neutral-400">
              <BookOpen size={12} />
              <span className="font-medium">Page {source.metadata.page}</span>
            </div>
          )}
        </div>

        {/* Relevance badge */}
        <div className="flex-shrink-0">
          <span
            className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg font-semibold
                       border transition-all duration-150 ${relevanceBadge.color}`}
            title={relevanceBadge.label}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60"></span>
            {formatScore(source.metadata.score)}%
          </span>
        </div>
      </button>

      {/* Expandable content */}
      {isExpanded && (
        <div className="px-4 pb-4 animate-slide-up">
          <div className="pt-3 border-t border-neutral-200 dark:border-neutral-800">
            {/* Content preview */}
            <div className="bg-neutral-50 dark:bg-neutral-900/50 rounded-xl p-4 border border-neutral-200 dark:border-neutral-800">
              <p className="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed whitespace-pre-wrap">
                {source.content}
              </p>
            </div>
            {/* Optional: Metadata footer */}
            <div className="mt-3 flex items-center gap-4 text-xs text-neutral-500 dark:text-neutral-400">
              <span className="flex items-center gap-1">
                <span className="font-medium">Source {index + 1}</span>
              </span>
              <span className="flex items-center gap-1">
                <span className="w-1 h-1 rounded-full bg-neutral-400 dark:bg-neutral-600"></span>
                <span>{relevanceBadge.label}</span>
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
