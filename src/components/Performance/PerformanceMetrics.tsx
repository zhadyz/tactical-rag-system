import React from 'react';
import { Clock, Zap, Database, Activity, TrendingUp, TrendingDown } from 'lucide-react';
import type { TimingBreakdown } from '../../types';

interface PerformanceMetricsProps {
  timeMs: number;
  breakdown?: TimingBreakdown;
  cacheHit?: boolean;
  strategyUsed?: string;
  queryType?: string;
  mode?: string;
  compact?: boolean;
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
  timeMs,
  breakdown,
  cacheHit,
  strategyUsed,
  queryType,
  mode,
  compact = false,
}) => {
  // Calculate performance grade
  const getPerformanceGrade = (ms: number): { grade: string; color: string; bgColor: string; description: string } => {
    if (ms < 1000) {
      return {
        grade: 'S+',
        color: 'text-green-800 dark:text-green-200',
        bgColor: 'bg-green-100 dark:bg-green-900',
        description: 'Exceptional',
      };
    } else if (ms < 3000) {
      return {
        grade: 'A',
        color: 'text-yellow-800 dark:text-yellow-200',
        bgColor: 'bg-yellow-100 dark:bg-yellow-900',
        description: 'Good',
      };
    } else if (ms < 5000) {
      return {
        grade: 'B',
        color: 'text-orange-800 dark:text-orange-200',
        bgColor: 'bg-orange-100 dark:bg-orange-900',
        description: 'Average',
      };
    } else {
      return {
        grade: 'C+',
        color: 'text-red-800 dark:text-red-200',
        bgColor: 'bg-red-100 dark:bg-red-900',
        description: 'Needs Improvement',
      };
    }
  };

  const performance = getPerformanceGrade(timeMs);
  const timeSec = (timeMs / 1000).toFixed(2);

  // Sort stages by time for better visualization
  const sortedStages = breakdown
    ? Object.entries(breakdown.stages).sort(([, a], [, b]) => b.time_ms - a.time_ms)
    : [];

  // Get stage color based on percentage
  const getStageColor = (percentage: number): string => {
    if (percentage >= 40) return 'bg-red-500';
    if (percentage >= 20) return 'bg-orange-500';
    if (percentage >= 10) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2 text-xs">
        <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md ${performance.bgColor} ${performance.color} font-semibold`}>
          <Clock size={12} />
          <span className="font-mono">{timeSec}s</span>
          <span className="font-bold">{performance.grade}</span>
        </div>
        {cacheHit && (
          <div className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
            <Zap size={12} />
            <span>Cached</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header: Overall Performance */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${performance.bgColor} ${performance.color}`}>
              <Clock size={20} />
              <div className="text-left">
                <div className="text-2xl font-bold font-mono">{timeSec}s</div>
                <div className="text-xs font-semibold">{performance.description}</div>
              </div>
            </div>

            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 ${performance.bgColor} ${performance.color}`}>
              <Activity size={20} />
              <div className="text-3xl font-bold">{performance.grade}</div>
            </div>
          </div>

          {/* Metadata badges */}
          <div className="flex flex-wrap gap-2">
            {cacheHit && (
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm font-medium">
                <Zap size={14} />
                <span>Cache Hit</span>
              </div>
            )}
            {strategyUsed && (
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-sm">
                <Database size={14} />
                <span>{strategyUsed}</span>
              </div>
            )}
            {queryType && (
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm">
                <span>{queryType}</span>
              </div>
            )}
            {mode && (
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm">
                <span>Mode: {mode}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Timing Breakdown */}
      {breakdown && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
            <TrendingUp size={16} />
            Timing Breakdown
          </h4>

          {/* Visual bar chart */}
          <div className="space-y-2">
            {sortedStages.map(([stageName, stage]) => (
              <div key={stageName} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-gray-700 dark:text-gray-300">
                    {stageName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-gray-600 dark:text-gray-400">
                      {stage.time_ms.toFixed(1)}ms
                    </span>
                    <span className="font-semibold text-gray-700 dark:text-gray-300">
                      {stage.percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="relative h-6 bg-gray-200 dark:bg-gray-700 rounded-md overflow-hidden">
                  <div
                    className={`h-full ${getStageColor(stage.percentage)} transition-all duration-500 ease-out flex items-center justify-end px-2`}
                    style={{ width: `${stage.percentage}%` }}
                  >
                    {stage.percentage > 15 && (
                      <span className="text-white text-xs font-bold">
                        {stage.percentage.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Unaccounted time */}
            {breakdown.unaccounted_ms > 0 && (
              <div className="space-y-1 opacity-60">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-gray-600 dark:text-gray-400">
                    Unaccounted
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-gray-500 dark:text-gray-500">
                      {breakdown.unaccounted_ms.toFixed(1)}ms
                    </span>
                    <span className="font-semibold text-gray-600 dark:text-gray-400">
                      {breakdown.unaccounted_percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>

                <div className="relative h-4 bg-gray-200 dark:bg-gray-700 rounded-md overflow-hidden">
                  <div
                    className="h-full bg-gray-400 dark:bg-gray-600 transition-all duration-500 ease-out"
                    style={{ width: `${breakdown.unaccounted_percentage}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Summary stats */}
          <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between text-sm">
              <span className="font-semibold text-gray-700 dark:text-gray-300">Total Time</span>
              <span className="font-mono font-bold text-gray-900 dark:text-gray-100">
                {breakdown.total_ms.toFixed(1)}ms
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Performance tips */}
      {!cacheHit && timeMs > 3000 && (
        <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <TrendingDown size={16} className="text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-amber-800 dark:text-amber-200">
            <p className="font-semibold mb-1">Performance Tip</p>
            <p>Consider enabling Redis caching for faster repeat queries.</p>
          </div>
        </div>
      )}
    </div>
  );
};
