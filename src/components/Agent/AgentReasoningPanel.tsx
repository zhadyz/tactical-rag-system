import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Search, CheckCircle, Shield, Loader2 } from 'lucide-react';
import type { AgentStep } from '../../types';
import useStore from '../../store/useStore';

const stepIcons: Record<AgentStep['type'], React.ReactNode> = {
  thinking: <Brain size={16} className="text-purple-500 dark:text-purple-400" />,
  tool_call: <Search size={16} className="text-blue-500 dark:text-blue-400" />,
  tool_result: <CheckCircle size={16} className="text-green-500 dark:text-green-400" />,
  crag_evaluation: <Shield size={16} className="text-amber-500 dark:text-amber-400" />,
  verification: <Shield size={16} className="text-teal-500 dark:text-teal-400" />,
};

const stepLabels: Record<AgentStep['type'], string> = {
  thinking: 'Thinking',
  tool_call: 'Tool Call',
  tool_result: 'Result',
  crag_evaluation: 'Quality Check',
  verification: 'Verification',
};

interface AgentReasoningPanelProps {
  steps?: AgentStep[];
  isActive?: boolean;
  collapsed?: boolean;
}

export const AgentReasoningPanel = React.memo<AgentReasoningPanelProps>(({
  steps: propSteps,
  isActive: propIsActive,
  collapsed = false,
}) => {
  const storeSteps = useStore((state) => state.currentSteps);
  const storeIsActive = useStore((state) => state.isAgentActive);
  const showAgentReasoning = useStore((state) => state.settings.showAgentReasoning);

  const steps = propSteps ?? storeSteps;
  const isActive = propIsActive ?? storeIsActive;

  const [isCollapsed, setIsCollapsed] = React.useState(collapsed);

  if (!showAgentReasoning || steps.length === 0) return null;

  return (
    <div className="mx-6 my-3">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200 dark:border-neutral-800 rounded-xl overflow-hidden"
      >
        {/* Header */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full flex items-center gap-2.5 px-4 py-3 hover:bg-neutral-100 dark:hover:bg-neutral-800/50 transition-colors"
        >
          {isActive ? (
            <Loader2 size={16} className="text-primary-500 animate-spin" />
          ) : (
            <Brain size={16} className="text-primary-500" />
          )}
          <span className="text-sm font-semibold text-neutral-800 dark:text-neutral-200">
            Agent Reasoning
          </span>
          <span className="text-xs text-neutral-500 dark:text-neutral-400 ml-auto">
            {steps.length} step{steps.length !== 1 ? 's' : ''}
          </span>
        </button>

        {/* Timeline */}
        <AnimatePresence>
          {!isCollapsed && (
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: 'auto' }}
              exit={{ height: 0 }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-3 space-y-1">
                {steps.map((step, idx) => (
                  <motion.div
                    key={step.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="flex items-start gap-2.5 py-1.5"
                  >
                    {/* Icon */}
                    <div className="flex-shrink-0 mt-0.5">
                      {step.status === 'running' ? (
                        <Loader2 size={16} className="text-primary-500 animate-spin" />
                      ) : (
                        stepIcons[step.type]
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
                          {stepLabels[step.type]}
                        </span>
                        {step.toolName && (
                          <span className="text-xs px-1.5 py-0.5 bg-neutral-200 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded font-mono">
                            {step.toolName}
                          </span>
                        )}
                        {step.durationMs !== undefined && (
                          <span className="text-xs text-neutral-400 dark:text-neutral-500 ml-auto">
                            {step.durationMs}ms
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate mt-0.5">
                        {step.content}
                      </p>
                    </div>
                  </motion.div>
                ))}

                {/* Active spinner at bottom */}
                {isActive && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex items-center gap-2 py-1.5 pl-0.5"
                  >
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-xs text-neutral-400">Processing...</span>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
});
