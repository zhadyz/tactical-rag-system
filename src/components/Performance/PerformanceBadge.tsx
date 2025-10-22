import React, { useState } from 'react';
import { Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { PerformanceMetrics } from './PerformanceMetrics';
import type { QueryMetadata } from '../../types';

interface PerformanceBadgeProps {
  metadata: QueryMetadata;
}

export const PerformanceBadge: React.FC<PerformanceBadgeProps> = ({ metadata }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const timeMs = metadata.processing_time_ms;
  const timeSec = (timeMs / 1000).toFixed(2);

  // Get performance grade and colors
  const getPerformanceStyle = (ms: number): { grade: string; colorClass: string } => {
    if (ms < 1000) {
      return {
        grade: 'S+',
        colorClass: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 border-green-300 dark:border-green-700',
      };
    } else if (ms < 3000) {
      return {
        grade: 'A',
        colorClass: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 border-yellow-300 dark:border-yellow-700',
      };
    } else if (ms < 5000) {
      return {
        grade: 'B',
        colorClass: 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 border-orange-300 dark:border-orange-700',
      };
    } else {
      return {
        grade: 'C+',
        colorClass: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 border-red-300 dark:border-red-700',
      };
    }
  };

  const performance = getPerformanceStyle(timeMs);

  return (
    <div className="mt-3 space-y-2">
      {/* Collapsed Badge */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`w-full flex items-center justify-between gap-3 px-3 py-2 rounded-lg border transition-all duration-200 hover:shadow-md ${performance.colorClass}`}
      >
        <div className="flex items-center gap-2">
          <Clock size={16} />
          <span className="text-sm font-semibold">Performance</span>
          <span className="font-mono font-bold text-base">{timeSec}s</span>
          <span className="font-bold text-base">{performance.grade}</span>
        </div>
        <div className="flex items-center gap-2">
          {metadata.cache_hit && (
            <span className="text-xs px-2 py-1 rounded bg-blue-200 dark:bg-blue-800 text-blue-900 dark:text-blue-100">
              Cached
            </span>
          )}
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="animate-slide-in p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <PerformanceMetrics
            timeMs={timeMs}
            breakdown={metadata.timing_breakdown}
            cacheHit={metadata.cache_hit}
            strategyUsed={metadata.strategy_used}
            queryType={metadata.query_type}
            mode={metadata.mode}
          />
        </div>
      )}
    </div>
  );
};
