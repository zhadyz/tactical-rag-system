import React from 'react';
import { Clock, TrendingUp, Zap, BarChart3, AlertCircle } from 'lucide-react';
import { usePerformanceStore } from '../../store/performanceStore';

interface TimingHistoryProps {
  limit?: number;
  showChart?: boolean;
}

export const TimingHistory: React.FC<TimingHistoryProps> = ({
  limit = 10,
  showChart = true,
}) => {
  const queryHistory = usePerformanceStore((state) => state.queryHistory);
  const stats = usePerformanceStore((state) => state.stats);

  // Get recent queries by slicing the history
  const recentQueries = queryHistory.slice(0, limit);

  if (recentQueries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <AlertCircle size={48} className="text-neutral-400 dark:text-neutral-600 mb-3" />
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          No query history yet. Start asking questions to see performance metrics.
        </p>
      </div>
    );
  }

  // Calculate max time for chart scaling
  const maxTime = Math.max(...recentQueries.map((q) => q.time_ms));

  // Get performance color
  const getPerformanceColor = (ms: number): string => {
    if (ms < 1000) return 'bg-green-500';
    if (ms < 3000) return 'bg-yellow-500';
    if (ms < 5000) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getPerformanceTextColor = (ms: number): string => {
    if (ms < 1000) return 'text-green-600 dark:text-green-400';
    if (ms < 3000) return 'text-yellow-600 dark:text-yellow-400';
    if (ms < 5000) return 'text-orange-600 dark:text-orange-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="space-y-6">
      {/* Statistics Summary */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={16} className="text-neutral-500" />
            <span className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
              Average Time
            </span>
          </div>
          <div className={`text-2xl font-bold font-mono ${getPerformanceTextColor(stats.avgTime)}`}>
            {(stats.avgTime / 1000).toFixed(2)}s
          </div>
        </div>

        <div className="p-4 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Zap size={16} className="text-blue-500" />
            <span className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
              Cache Hit Rate
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-blue-600 dark:text-blue-400">
            {stats.cacheHitRate.toFixed(0)}%
          </div>
        </div>

        <div className="p-4 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={16} className="text-green-500" />
            <span className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
              Fastest Query
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-green-600 dark:text-green-400">
            {(stats.fastestTime / 1000).toFixed(2)}s
          </div>
        </div>

        <div className="p-4 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 size={16} className="text-neutral-500" />
            <span className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
              Total Queries
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-neutral-700 dark:text-neutral-300">
            {stats.totalQueries}
          </div>
        </div>
      </div>

      {/* Cache Performance Comparison */}
      {stats.avgCachedTime > 0 && stats.avgUncachedTime > 0 && (
        <div className="p-4 bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-900/20 dark:to-green-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <h4 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-3">
            Cache Performance Impact
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-neutral-600 dark:text-neutral-400 mb-1">Cached Queries</div>
              <div className="text-lg font-bold font-mono text-blue-600 dark:text-blue-400">
                {(stats.avgCachedTime / 1000).toFixed(2)}s
              </div>
            </div>
            <div>
              <div className="text-xs text-neutral-600 dark:text-neutral-400 mb-1">Uncached Queries</div>
              <div className="text-lg font-bold font-mono text-neutral-600 dark:text-neutral-400">
                {(stats.avgUncachedTime / 1000).toFixed(2)}s
              </div>
            </div>
          </div>
          <div className="mt-2 text-xs text-green-700 dark:text-green-300">
            Cache provides {((stats.avgUncachedTime - stats.avgCachedTime) / stats.avgUncachedTime * 100).toFixed(0)}% speedup
          </div>
        </div>
      )}

      {/* Performance Trend Chart */}
      {showChart && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 flex items-center gap-2">
            <BarChart3 size={16} />
            Recent Performance Trend
          </h4>
          <div className="space-y-1">
            {recentQueries.map((query, idx) => {
              const barWidth = (query.time_ms / maxTime) * 100;
              const timeSec = (query.time_ms / 1000).toFixed(2);

              return (
                <div key={query.id} className="group">
                  <div className="flex items-center gap-2 text-xs mb-0.5">
                    <span className="text-neutral-500 dark:text-neutral-500 font-mono w-6">
                      #{recentQueries.length - idx}
                    </span>
                    <span className="flex-1 truncate text-neutral-600 dark:text-neutral-400">
                      {query.question}
                    </span>
                    <span className={`font-mono font-semibold ${getPerformanceTextColor(query.time_ms)}`}>
                      {timeSec}s
                    </span>
                    {query.cache_hit && (
                      <Zap size={12} className="text-blue-500" />
                    )}
                  </div>
                  <div className="relative h-5 bg-neutral-200 dark:bg-neutral-700 rounded-sm overflow-hidden">
                    <div
                      className={`h-full ${getPerformanceColor(query.time_ms)} transition-all duration-300 ease-out group-hover:opacity-80`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Queries List */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">
          Query Details
        </h4>
        <div className="space-y-2">
          {recentQueries.slice(0, 5).map((query) => (
            <div
              key={query.id}
              className="p-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <p className="text-sm text-neutral-900 dark:text-neutral-100 flex-1 line-clamp-2">
                  {query.question}
                </p>
                <span className={`text-sm font-bold font-mono ${getPerformanceTextColor(query.time_ms)}`}>
                  {(query.time_ms / 1000).toFixed(2)}s
                </span>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-neutral-500 dark:text-neutral-400">
                  {new Date(query.timestamp).toLocaleTimeString()}
                </span>
                {query.cache_hit && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs">
                    <Zap size={10} />
                    Cached
                  </span>
                )}
                {query.strategy_used && (
                  <span className="px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 text-xs">
                    {query.strategy_used}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
