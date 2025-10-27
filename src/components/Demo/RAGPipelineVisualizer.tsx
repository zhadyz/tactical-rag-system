import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Pause,
  RotateCcw,
  ChevronRight,
  FileText,
  Hash,
  Database,
  Search,
  TrendingUp,
  Sparkles,
  CheckCircle,
  Activity
} from 'lucide-react';
import type { PipelineStep, RAGPipelineData } from '../../types/demo';
import benchmarkData from '../../data/benchmarks.json';

interface RAGPipelineVisualizerProps {
  className?: string;
  mode?: 'gpu' | 'cpu';
}

export default function RAGPipelineVisualizer({ className = '', mode = 'gpu' }: RAGPipelineVisualizerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [pipelineData, setPipelineData] = useState<RAGPipelineData | null>(null);

  const pipelineSteps: PipelineStep[] = (benchmarkData.pipelineStages as any[]).map((stage, idx) => ({
    id: stage.id,
    name: stage.name,
    description: stage.description,
    timing: {
      gpu: stage.gpu,
      cpu: stage.cpu
    },
    details: {
      input: getStepInput(idx),
      output: getStepOutput(idx),
      explanation: stage.explanation
    },
    status: 'pending',
    progress: 0
  }));

  useEffect(() => {
    if (isPlaying && currentStep < pipelineSteps.length) {
      const timer = setTimeout(() => {
        setCurrentStep(currentStep + 1);
      }, pipelineSteps[currentStep].timing[mode] * 2); // Slow down for visibility

      return () => clearTimeout(timer);
    } else if (currentStep >= pipelineSteps.length) {
      setIsPlaying(false);
      // Generate final pipeline data
      setPipelineData({
        steps: pipelineSteps.map((step, idx) => ({
          ...step,
          status: idx <= currentStep ? 'complete' : 'pending',
          progress: idx < currentStep ? 100 : idx === currentStep ? 50 : 0
        })),
        totalTiming: {
          gpu: pipelineSteps.reduce((acc, s) => acc + s.timing.gpu, 0),
          cpu: pipelineSteps.reduce((acc, s) => acc + s.timing.cpu, 0)
        },
        document: {
          name: 'AFM 200-1: Fundamentals of Air Force Leadership',
          size: 892000,
          chunks: 156
        },
        query: 'What are the key principles of Air Force leadership?',
        answer: 'The key principles of Air Force leadership include integrity, service before self, and excellence in all we do...'
      });
    }
  }, [isPlaying, currentStep]);

  const reset = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    setSelectedStep(null);
    setPipelineData(null);
  };

  const togglePlay = () => {
    if (currentStep >= pipelineSteps.length) {
      reset();
    }
    setIsPlaying(!isPlaying);
  };

  const getStepIcon = (stepId: string) => {
    const icons: Record<string, React.ReactNode> = {
      chunking: <FileText className="w-5 h-5" />,
      embedding: <Hash className="w-5 h-5" />,
      storage: <Database className="w-5 h-5" />,
      query_embedding: <Hash className="w-5 h-5" />,
      retrieval: <Search className="w-5 h-5" />,
      reranking: <TrendingUp className="w-5 h-5" />,
      generation: <Sparkles className="w-5 h-5" />,
      confidence: <CheckCircle className="w-5 h-5" />
    };
    return icons[stepId] || <Activity className="w-5 h-5" />;
  };

  return (
    <div className={`bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 border border-slate-700 ${className}`}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">RAG Pipeline Visualizer</h2>
              <p className="text-slate-400">Step-by-step breakdown with real timings</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={togglePlay}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 rounded-xl font-semibold text-white transition-all shadow-lg shadow-blue-500/20"
            >
              {isPlaying ? (
                <>
                  <Pause className="w-5 h-5" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  {currentStep > 0 ? 'Resume' : 'Start'}
                </>
              )}
            </button>
            {currentStep > 0 && (
              <button
                onClick={reset}
                className="p-3 bg-slate-700 hover:bg-slate-600 rounded-xl transition-colors"
              >
                <RotateCcw className="w-5 h-5 text-white" />
              </button>
            )}
          </div>
        </div>

        {/* Mode Toggle */}
        <div className="flex gap-2">
          <span className="text-sm text-slate-400">Mode:</span>
          <span className="text-sm font-semibold text-white">
            {mode === 'gpu' ? 'GPU Accelerated' : 'CPU Only'}
          </span>
        </div>
      </div>

      {/* Pipeline Flow */}
      <div className="mb-8 relative">
        {/* Connection Lines */}
        <div className="absolute top-12 left-0 right-0 h-0.5 bg-slate-700 z-0" />

        {/* Steps */}
        <div className="grid grid-cols-4 gap-4 relative z-10">
          {pipelineSteps.map((step, idx) => (
            <PipelineStepCard
              key={step.id}
              step={step}
              index={idx}
              isActive={idx === currentStep}
              isComplete={idx < currentStep}
              isPending={idx > currentStep}
              onClick={() => setSelectedStep(idx)}
              isSelected={selectedStep === idx}
              mode={mode}
            />
          ))}
        </div>
      </div>

      {/* Step Details */}
      <AnimatePresence mode="wait">
        {selectedStep !== null && (
          <StepDetails
            step={pipelineSteps[selectedStep]}
            mode={mode}
            onClose={() => setSelectedStep(null)}
          />
        )}
      </AnimatePresence>

      {/* Total Timing */}
      {currentStep > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 bg-slate-800/50 rounded-xl p-6 border border-slate-700"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white mb-2">Pipeline Progress</h3>
              <div className="flex items-center gap-4">
                <span className="text-sm text-slate-400">
                  Step {currentStep} of {pipelineSteps.length}
                </span>
                <div className="h-2 w-48 bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${(currentStep / pipelineSteps.length) * 100}%` }}
                  />
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400">Elapsed Time</div>
              <div className="text-2xl font-bold text-white">
                {pipelineSteps
                  .slice(0, currentStep)
                  .reduce((acc, s) => acc + s.timing[mode], 0)}ms
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

interface PipelineStepCardProps {
  step: PipelineStep;
  index: number;
  isActive: boolean;
  isComplete: boolean;
  isPending: boolean;
  onClick: () => void;
  isSelected: boolean;
  mode: 'gpu' | 'cpu';
}

function PipelineStepCard({
  step,
  index,
  isActive,
  isComplete,
  isPending,
  onClick,
  isSelected,
  mode
}: PipelineStepCardProps) {
  const getStepIcon = (stepId: string) => {
    const icons: Record<string, React.ReactNode> = {
      chunking: <FileText className="w-5 h-5" />,
      embedding: <Hash className="w-5 h-5" />,
      storage: <Database className="w-5 h-5" />,
      query_embedding: <Hash className="w-5 h-5" />,
      retrieval: <Search className="w-5 h-5" />,
      reranking: <TrendingUp className="w-5 h-5" />,
      generation: <Sparkles className="w-5 h-5" />,
      confidence: <CheckCircle className="w-5 h-5" />
    };
    return icons[stepId] || <Activity className="w-5 h-5" />;
  };

  return (
    <motion.div
      onClick={onClick}
      className={`relative cursor-pointer transition-all ${
        isSelected ? 'scale-105' : 'scale-100'
      }`}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.98 }}
    >
      <div
        className={`rounded-xl p-4 border ${
          isComplete
            ? 'bg-green-500/10 border-green-500/50'
            : isActive
            ? 'bg-blue-500/10 border-blue-500/50 animate-pulse'
            : isPending
            ? 'bg-slate-800/50 border-slate-700'
            : 'bg-slate-800/50 border-slate-700'
        }`}
      >
        {/* Status Indicator */}
        <div className="flex items-center justify-between mb-3">
          <div
            className={`p-2 rounded-lg ${
              isComplete
                ? 'bg-green-500'
                : isActive
                ? 'bg-blue-500'
                : 'bg-slate-700'
            }`}
          >
            {getStepIcon(step.id)}
          </div>
          <span className="text-xs font-bold text-slate-400">#{index + 1}</span>
        </div>

        {/* Name */}
        <h4 className="font-semibold text-white text-sm mb-2 line-clamp-2">
          {step.name}
        </h4>

        {/* Timing */}
        <div className="text-xs text-slate-400">
          {step.timing[mode]}ms
        </div>

        {/* Progress Bar */}
        {isActive && (
          <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
              initial={{ width: 0 }}
              animate={{ width: '100%' }}
              transition={{ duration: step.timing[mode] / 1000 }}
            />
          </div>
        )}
      </div>

      {/* Arrow Connector */}
      {index < 7 && (
        <ChevronRight className="absolute -right-6 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-600" />
      )}
    </motion.div>
  );
}

interface StepDetailsProps {
  step: PipelineStep;
  mode: 'gpu' | 'cpu';
  onClose: () => void;
}

function StepDetails({ step, mode, onClose }: StepDetailsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 overflow-hidden"
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">{step.name}</h3>
          <p className="text-slate-400">{step.description}</p>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
        >
          <span className="text-slate-400">✕</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input */}
        <div>
          <h4 className="text-sm font-semibold text-slate-300 mb-2">Input</h4>
          <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
            <code className="text-xs text-slate-300 font-mono whitespace-pre-wrap">
              {step.details.input}
            </code>
          </div>
        </div>

        {/* Output */}
        <div>
          <h4 className="text-sm font-semibold text-slate-300 mb-2">Output</h4>
          <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
            <code className="text-xs text-slate-300 font-mono whitespace-pre-wrap">
              {step.details.output}
            </code>
          </div>
        </div>

        {/* Explanation */}
        <div className="md:col-span-2">
          <h4 className="text-sm font-semibold text-slate-300 mb-2">How It Works</h4>
          <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/30">
            <p className="text-sm text-slate-300">{step.details.explanation}</p>
          </div>
        </div>

        {/* Timing Comparison */}
        <div className="md:col-span-2">
          <h4 className="text-sm font-semibold text-slate-300 mb-3">Performance Comparison</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-purple-500/10 rounded-lg p-4 border border-purple-500/30">
              <div className="text-xs text-slate-400 mb-1">GPU Accelerated</div>
              <div className="text-2xl font-bold text-purple-400">{step.timing.gpu}ms</div>
            </div>
            <div className="bg-orange-500/10 rounded-lg p-4 border border-orange-500/30">
              <div className="text-xs text-slate-400 mb-1">CPU Only</div>
              <div className="text-2xl font-bold text-orange-400">{step.timing.cpu}ms</div>
            </div>
          </div>
          {step.timing.gpu !== step.timing.cpu && (
            <div className="mt-2 text-sm text-green-400">
              ⚡ {(step.timing.cpu / step.timing.gpu).toFixed(1)}x speedup with GPU
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// Helper functions for step input/output
function getStepInput(idx: number): string {
  const inputs = [
    'Raw PDF document (892KB)',
    'Document chunks (156 chunks)',
    'Vector embeddings (384-dim)',
    'User query text',
    'Query embedding (384-dim)',
    'Top 20 candidate chunks',
    'Top 5 reranked chunks',
    'Generated answer text'
  ];
  return inputs[idx] || 'Processing...';
}

function getStepOutput(idx: number): string {
  const outputs = [
    '156 semantic chunks\n~512 chars each',
    '156 embeddings\n[0.23, -0.45, ...]',
    'Stored in Qdrant\nindex_name: documents',
    'Query embedding\n[0.12, -0.67, ...]',
    '20 similar chunks\nscore: 0.85 - 0.72',
    '5 top chunks\nscore: 0.92 - 0.85',
    'Answer: "The key principles..."\n~250 words',
    'Confidence: 87%\nsignals: retrieval=0.9, ...'
  ];
  return outputs[idx] || 'Complete';
}
