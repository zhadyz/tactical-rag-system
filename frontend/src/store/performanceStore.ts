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
  maxHistorySize: number;

  // Actions
  addQuery: (query: PerformanceQuery) => void;
  getStats: () => PerformanceStats;
  getRecentQueries: (limit?: number) => PerformanceQuery[];
  clearHistory: () => void;
  getLatestQuery: () => PerformanceQuery | null;
}

export const usePerformanceStore = create<PerformanceStore>((set, get) => ({
  queryHistory: [],
  maxHistorySize: 50, // Keep last 50 queries in memory

  addQuery: (query) =>
    set((state) => {
      const newHistory = [query, ...state.queryHistory].slice(
        0,
        state.maxHistorySize
      );
      return { queryHistory: newHistory };
    }),

  getStats: () => {
    const { queryHistory } = get();

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

    return {
      avgTime: times.reduce((sum, time) => sum + time, 0) / times.length,
      fastestTime: Math.min(...times),
      slowestTime: Math.max(...times),
      cacheHitRate: (cacheHits / queryHistory.length) * 100,
      totalQueries: queryHistory.length,
      avgCachedTime,
      avgUncachedTime,
    };
  },

  getRecentQueries: (limit = 10) => {
    const { queryHistory } = get();
    return queryHistory.slice(0, limit);
  },

  clearHistory: () => set({ queryHistory: [] }),

  getLatestQuery: () => {
    const { queryHistory } = get();
    return queryHistory.length > 0 ? queryHistory[0] : null;
  },
}));
