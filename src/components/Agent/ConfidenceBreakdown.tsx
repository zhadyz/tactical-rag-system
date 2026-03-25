import React from 'react';
import { Activity } from 'lucide-react';

interface ConfidenceBreakdownProps {
  confidence: number;
  signals?: Record<string, number>;
}

const getConfidenceColor = (value: number): string => {
  if (value >= 0.8) return 'text-green-600 dark:text-green-400';
  if (value >= 0.6) return 'text-amber-600 dark:text-amber-400';
  return 'text-red-600 dark:text-red-400';
};

const getBarColor = (value: number): string => {
  if (value >= 0.8) return 'bg-green-500';
  if (value >= 0.6) return 'bg-amber-500';
  return 'bg-red-500';
};

const signalLabels: Record<string, string> = {
  retrieval: 'Retrieval Quality',
  reranking: 'Reranking Score',
  crag: 'CRAG Gate',
  source_agreement: 'Source Agreement',
  answer_coverage: 'Answer Coverage',
  verification: 'Claim Verification',
};

export const ConfidenceBreakdown: React.FC<ConfidenceBreakdownProps> = ({
  confidence,
  signals,
}) => {
  return (
    <div className="bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 rounded-xl p-4">
      {/* Overall confidence */}
      <div className="flex items-center gap-3 mb-4">
        <Activity size={16} className="text-primary-500" />
        <span className="text-sm font-semibold text-neutral-800 dark:text-neutral-200">
          Confidence
        </span>
        <span className={`text-lg font-bold ml-auto ${getConfidenceColor(confidence)}`}>
          {(confidence * 100).toFixed(0)}%
        </span>
      </div>

      {/* Overall bar */}
      <div className="h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden mb-4">
        <div
          className={`h-full ${getBarColor(confidence)} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(confidence * 100, 100)}%` }}
        />
      </div>

      {/* Signal breakdown */}
      {signals && Object.keys(signals).length > 0 && (
        <div className="space-y-2.5">
          {Object.entries(signals).map(([key, value]) => (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-neutral-600 dark:text-neutral-400">
                  {signalLabels[key] || key}
                </span>
                <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300">
                  {(value * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-1 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getBarColor(value)} rounded-full transition-all duration-300`}
                  style={{ width: `${Math.min(value * 100, 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
