import { create } from 'zustand';
import type { TimingBreakdown } from '../types';

export interface PerformanceQuery {
  id: string;
  timestamp: string;
  question: string;
  time_ms: number;
  cache_hit: boolean;
  breakdown?: TimingBreakdown;
  strategy_used?: string;
  query_type?: string;
  mode?: string;
}

export interface PerformanceStats {
  avgTime: number;
  fastestTime: number;
  slowestTime: number;
  cacheHitRate: number;
  totalQueries: number;
  avgCachedTime: number;
  avgUncachedTime: number;
}

interface PerformanceStore {
  queryHistory: PerformanceQuery[];
  stats: PerformanceStats;
  maxHistorySize: number;

  // Actions
  addQuery: (query: PerformanceQuery) => void;
  clearHistory: () => void;
}

// PERFORMANCE OPTIMIZATION: Memoization cache for stats computation
// This prevents unnecessary recalculation when history hasn't changed
let cachedStats: PerformanceStats | null = null;
let cachedHistoryLength = 0;
let cachedHistoryChecksum = '';

// Create a simple checksum from query history to detect changes
const createHistoryChecksum = (queryHistory: PerformanceQuery[]): string => {
  if (queryHistory.length === 0) return '';
  // Use first and last query IDs plus length as a lightweight checksum
  return `${queryHistory.length}-${queryHistory[0]?.id}-${queryHistory[queryHistory.length - 1]?.id}`;
};

// Helper function to compute stats from query history (now with memoization)
const computeStats = (queryHistory: PerformanceQuery[]): PerformanceStats => {
  // OPTIMIZATION: Check if we can return cached stats
  const currentChecksum = createHistoryChecksum(queryHistory);
  if (
    cachedStats !== null &&
    queryHistory.length === cachedHistoryLength &&
    currentChecksum === cachedHistoryChecksum
  ) {
    return cachedStats;
  }

  // Empty history - no need to cache
  if (queryHistory.length === 0) {
    return {
      avgTime: 0,
      fastestTime: 0,
      slowestTime: 0,
      cacheHitRate: 0,
      totalQueries: 0,
      avgCachedTime: 0,
      avgUncachedTime: 0,
    };
  }

  // Compute stats (expensive operation)
  const times = queryHistory.map((q) => q.time_ms);
  const cacheHits = queryHistory.filter((q) => q.cache_hit).length;

  const cachedQueries = queryHistory.filter((q) => q.cache_hit);
  const uncachedQueries = queryHistory.filter((q) => !q.cache_hit);

  const avgCachedTime = cachedQueries.length > 0
    ? cachedQueries.reduce((sum, q) => sum + q.time_ms, 0) / cachedQueries.length
    : 0;

  const avgUncachedTime = uncachedQueries.length > 0
    ? uncachedQueries.reduce((sum, q) => sum + q.time_ms, 0) / uncachedQueries.length
    : 0;

  const newStats = {
    avgTime: times.reduce((sum, time) => sum + time, 0) / times.length,
    fastestTime: Math.min(...times),
    slowestTime: Math.max(...times),
    cacheHitRate: (cacheHits / queryHistory.length) * 100,
    totalQueries: queryHistory.length,
    avgCachedTime,
    avgUncachedTime,
  };

  // Update cache
  cachedStats = newStats;
  cachedHistoryLength = queryHistory.length;
  cachedHistoryChecksum = currentChecksum;

  return newStats;
};

export const usePerformanceStore = create<PerformanceStore>((set) => ({
  queryHistory: [],
  stats: {
    avgTime: 0,
    fastestTime: 0,
    slowestTime: 0,
    cacheHitRate: 0,
    totalQueries: 0,
    avgCachedTime: 0,
    avgUncachedTime: 0,
  },
  maxHistorySize: 50, // Keep last 50 queries in memory

  addQuery: (query) =>
    set((state) => {
      const newHistory = [query, ...state.queryHistory].slice(
        0,
        state.maxHistorySize
      );
      const newStats = computeStats(newHistory);
      return { queryHistory: newHistory, stats: newStats };
    }),

  clearHistory: () => {
    // Clear memoization cache when history is cleared
    cachedStats = null;
    cachedHistoryLength = 0;
    cachedHistoryChecksum = '';

    set({
      queryHistory: [],
      stats: {
        avgTime: 0,
        fastestTime: 0,
        slowestTime: 0,
        cacheHitRate: 0,
        totalQueries: 0,
        avgCachedTime: 0,
        avgUncachedTime: 0,
      },
    });
  },
}));
