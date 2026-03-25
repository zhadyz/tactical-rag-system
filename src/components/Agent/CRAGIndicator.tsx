import React from 'react';
import { CheckCircle, XCircle, HelpCircle } from 'lucide-react';
import type { CRAGEvaluation } from '../../types';

interface CRAGIndicatorProps {
  evaluation: CRAGEvaluation;
}

const verdictConfig = {
  correct: {
    icon: CheckCircle,
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-100 dark:bg-green-900/30',
    border: 'border-green-200 dark:border-green-800/50',
    label: 'Verified',
  },
  incorrect: {
    icon: XCircle,
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900/30',
    border: 'border-red-200 dark:border-red-800/50',
    label: 'Low Quality',
  },
  ambiguous: {
    icon: HelpCircle,
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    border: 'border-amber-200 dark:border-amber-800/50',
    label: 'Uncertain',
  },
};

export const CRAGIndicator: React.FC<CRAGIndicatorProps> = ({ evaluation }) => {
  const config = verdictConfig[evaluation.verdict];
  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border ${config.bg} ${config.border} ${config.color} font-medium`}
      title={`CRAG Score: ${(evaluation.score * 100).toFixed(0)}%${evaluation.reason ? ` - ${evaluation.reason}` : ''}`}
    >
      <Icon size={12} />
      <span>{config.label}</span>
    </span>
  );
};
