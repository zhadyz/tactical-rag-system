import React from 'react';
import { ShieldCheck, ShieldAlert } from 'lucide-react';
import type { VerificationResult } from '../../types';

interface VerificationBadgeProps {
  results: VerificationResult[];
}

export const VerificationBadge: React.FC<VerificationBadgeProps> = ({ results }) => {
  if (results.length === 0) return null;

  const supported = results.filter((r) => r.supported).length;
  const total = results.length;

  return (
    <div className="mt-4 bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 rounded-xl p-4">
      {/* Summary header */}
      <div className="flex items-center gap-2 mb-3">
        <ShieldCheck size={16} className="text-primary-500" />
        <span className="text-sm font-semibold text-neutral-800 dark:text-neutral-200">
          Verification
        </span>
        <span className="text-xs text-neutral-500 dark:text-neutral-400 ml-auto">
          {supported}/{total} claims supported
        </span>
      </div>

      {/* Claims list */}
      <div className="space-y-2">
        {results.map((result, idx) => (
          <div
            key={idx}
            className="flex items-start gap-2.5 py-1.5"
          >
            {result.supported ? (
              <ShieldCheck
                size={14}
                className="flex-shrink-0 mt-0.5 text-green-500 dark:text-green-400"
              />
            ) : (
              <ShieldAlert
                size={14}
                className="flex-shrink-0 mt-0.5 text-amber-500 dark:text-amber-400"
              />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs text-neutral-700 dark:text-neutral-300 leading-relaxed">
                {result.claim}
              </p>
              {result.explanation && (
                <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                  {result.explanation}
                </p>
              )}
              {result.supportingSources.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {result.supportingSources.map((src, sIdx) => (
                    <span
                      key={sIdx}
                      className="text-[10px] px-1.5 py-0.5 bg-neutral-200 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded"
                    >
                      {src}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <span className="text-xs text-neutral-400 dark:text-neutral-500 flex-shrink-0">
              {(result.confidence * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
