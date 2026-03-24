import React from 'react';
import { Search, Clock, TrendingUp, FileText } from 'lucide-react';
import type { RetrievalStage } from '../../types';

interface RetrievalStageViewerProps {
  stages: RetrievalStage[];
}

export const RetrievalStageViewer: React.FC<RetrievalStageViewerProps> = ({ stages }) => {
  if (stages.length === 0) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {stages.map((stage, idx) => (
        <div
          key={idx}
          className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
              <Search size={16} className="text-primary-600 dark:text-primary-400" />
            </div>
            <h4 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 truncate">
              {stage.stageName}
            </h4>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 text-neutral-500 dark:text-neutral-400">
                <FileText size={12} />
                Results
              </span>
              <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                {stage.resultsCount}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 text-neutral-500 dark:text-neutral-400">
                <TrendingUp size={12} />
                Top Score
              </span>
              <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                {(stage.topScore * 100).toFixed(1)}%
              </span>
            </div>

            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 text-neutral-500 dark:text-neutral-400">
                <Clock size={12} />
                Duration
              </span>
              <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                {stage.durationMs}ms
              </span>
            </div>

            {/* Score bar */}
            <div className="mt-1">
              <div className="h-1.5 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary-500 to-primary-400 rounded-full transition-all"
                  style={{ width: `${Math.min(stage.topScore * 100, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
