import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap,
  Cpu,
  Upload,
  Play,
  RotateCcw,
  Download,
  Clock,
  TrendingUp,
  CheckCircle2,
  Loader2
} from 'lucide-react';
import type { RaceResult, RaceStage, RaceDocument, RaceConfig } from '../../types/demo';
import benchmarkData from '../../data/benchmarks.json';

interface PerformanceRaceProps {
  className?: string;
}

export default function PerformanceRace({ className = '' }: PerformanceRaceProps) {
  const [isRacing, setIsRacing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<RaceDocument | null>(null);
  const [gpuResult, setGpuResult] = useState<RaceResult | null>(null);
  const [cpuResult, setCpuResult] = useState<RaceResult | null>(null);
  const [raceConfig, setRaceConfig] = useState<RaceConfig>({
    document: benchmarkData.sampleDocuments[0] as any,
    query: 'What are the key principles of Air Force leadership?',
    modelSize: '7B',
    chunkSize: 512,
    topK: 5
  });

  const canvasRef = useRef<HTMLCanvasElement>(null);

  const stages: Array<{ name: string; gpuTime: number; cpuTime: number }> = [
    { name: 'Document Chunking', gpuTime: 45, cpuTime: 45 },
    { name: 'Embedding Generation', gpuTime: 120, cpuTime: 580 },
    { name: 'Vector Storage', gpuTime: 35, cpuTime: 35 },
    { name: 'Query Embedding', gpuTime: 25, cpuTime: 120 },
    { name: 'Vector Retrieval', gpuTime: 55, cpuTime: 55 },
    { name: 'LLM Reranking', gpuTime: 400, cpuTime: 1250 },
    { name: 'Answer Generation', gpuTime: 500, cpuTime: 1800 },
    { name: 'Confidence Scoring', gpuTime: 100, cpuTime: 100 }
  ];

  const startRace = async () => {
    setIsRacing(true);
    setIsComplete(false);
    setGpuResult(null);
    setCpuResult(null);

    // Simulate GPU pipeline
    const gpuStages: RaceStage[] = [];
    let gpuTime = 0;

    // Simulate CPU pipeline
    const cpuStages: RaceStage[] = [];
    let cpuTime = 0;

    // Run both pipelines in parallel with realistic timing
    for (let i = 0; i < stages.length; i++) {
      const stage = stages[i];

      // GPU stage
      const gpuStage: RaceStage = {
        name: stage.name,
        startTime: gpuTime,
        endTime: gpuTime + stage.gpuTime,
        duration: stage.gpuTime,
        status: 'running'
      };
      gpuStages.push(gpuStage);

      // CPU stage
      const cpuStage: RaceStage = {
        name: stage.name,
        startTime: cpuTime,
        endTime: cpuTime + stage.cpuTime,
        duration: stage.cpuTime,
        status: 'running'
      };
      cpuStages.push(cpuStage);

      // Update GPU result
      setGpuResult({
        pipeline: 'gpu',
        stages: [...gpuStages],
        totalTime: gpuTime + stage.gpuTime,
        tokensPerSecond: 85,
        memoryUsage: 6800
      });

      // Update CPU result
      setCpuResult({
        pipeline: 'cpu',
        stages: [...cpuStages],
        totalTime: cpuTime + stage.cpuTime,
        tokensPerSecond: 28,
        memoryUsage: 8500
      });

      gpuTime += stage.gpuTime;
      cpuTime += stage.cpuTime;

      // Wait for animation frame
      await new Promise(resolve => setTimeout(resolve, Math.max(stage.gpuTime, stage.cpuTime)));

      // Mark stages as complete
      gpuStage.status = 'complete';
      cpuStage.status = 'complete';
    }

    setIsComplete(true);
    setIsRacing(false);
  };

  const reset = () => {
    setIsComplete(false);
    setGpuResult(null);
    setCpuResult(null);
  };

  const exportResults = () => {
    if (!gpuResult || !cpuResult) return;

    const data = {
      timestamp: new Date().toISOString(),
      config: raceConfig,
      results: {
        gpu: gpuResult,
        cpu: cpuResult,
        speedup: (cpuResult.totalTime / gpuResult.totalTime).toFixed(2) + 'x',
        timeSaved: cpuResult.totalTime - gpuResult.totalTime
      }
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `apollo-performance-race-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedDocument({
      name: file.name,
      size: file.size,
      chunks: Math.ceil(file.size / 512)
    });

    setRaceConfig({
      ...raceConfig,
      document: {
        name: file.name,
        size: file.size,
        chunks: Math.ceil(file.size / 512)
      }
    });
  };

  const gpuProgress = gpuResult ? (gpuResult.totalTime / stages.reduce((acc, s) => acc + s.gpuTime, 0)) * 100 : 0;
  const cpuProgress = cpuResult ? (cpuResult.totalTime / stages.reduce((acc, s) => acc + s.cpuTime, 0)) * 100 : 0;

  const speedup = gpuResult && cpuResult ? (cpuResult.totalTime / gpuResult.totalTime) : 0;

  return (
    <div className={`bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 border border-slate-700 ${className}`}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">GPU vs CPU Performance Race</h2>
            <p className="text-slate-400">Watch both pipelines race side-by-side</p>
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Document Upload */}
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Document
          </label>
          <div className="relative">
            <input
              type="file"
              onChange={handleFileUpload}
              className="hidden"
              id="doc-upload"
              accept=".pdf,.txt,.md"
            />
            <label
              htmlFor="doc-upload"
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg cursor-pointer transition-colors"
            >
              <Upload className="w-4 h-4 text-slate-300" />
              <span className="text-sm text-slate-300">
                {selectedDocument?.name || raceConfig.document.name}
              </span>
            </label>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {Math.round((selectedDocument?.size || raceConfig.document.size) / 1024)}KB, {selectedDocument?.chunks || raceConfig.document.chunks} chunks
          </p>
        </div>

        {/* Query */}
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Query
          </label>
          <input
            type="text"
            value={raceConfig.query}
            onChange={(e) => setRaceConfig({ ...raceConfig, query: e.target.value })}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Enter your question..."
          />
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={startRace}
          disabled={isRacing}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed rounded-xl font-semibold text-white transition-all shadow-lg shadow-purple-500/20"
        >
          {isRacing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Racing...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Start Race
            </>
          )}
        </button>

        {isComplete && (
          <>
            <button
              onClick={reset}
              className="flex items-center gap-2 px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-xl font-semibold text-white transition-colors"
            >
              <RotateCcw className="w-5 h-5" />
              Reset
            </button>

            <button
              onClick={exportResults}
              className="flex items-center gap-2 px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-xl font-semibold text-white transition-colors"
            >
              <Download className="w-5 h-5" />
              Export
            </button>
          </>
        )}
      </div>

      {/* Race Tracks */}
      <div className="space-y-6">
        {/* GPU Track */}
        <RaceTrack
          label="GPU Accelerated"
          icon={<Zap className="w-5 h-5" />}
          color="from-purple-500 to-blue-500"
          result={gpuResult}
          progress={gpuProgress}
          isWinner={isComplete && speedup > 1}
        />

        {/* CPU Track */}
        <RaceTrack
          label="CPU Only"
          icon={<Cpu className="w-5 h-5" />}
          color="from-orange-500 to-red-500"
          result={cpuResult}
          progress={cpuProgress}
          isWinner={false}
        />
      </div>

      {/* Results */}
      {isComplete && gpuResult && cpuResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <MetricCard
            icon={<TrendingUp className="w-5 h-5" />}
            label="Speedup"
            value={`${speedup.toFixed(2)}x`}
            color="text-green-400"
          />
          <MetricCard
            icon={<Clock className="w-5 h-5" />}
            label="Time Saved"
            value={`${((cpuResult.totalTime - gpuResult.totalTime) / 1000).toFixed(2)}s`}
            color="text-blue-400"
          />
          <MetricCard
            icon={<CheckCircle2 className="w-5 h-5" />}
            label="GPU Winner"
            value={`${(((cpuResult.totalTime - gpuResult.totalTime) / cpuResult.totalTime) * 100).toFixed(0)}% faster`}
            color="text-purple-400"
          />
        </motion.div>
      )}
    </div>
  );
}

interface RaceTrackProps {
  label: string;
  icon: React.ReactNode;
  color: string;
  result: RaceResult | null;
  progress: number;
  isWinner: boolean;
}

function RaceTrack({ label, icon, color, result, progress, isWinner }: RaceTrackProps) {
  return (
    <div className="bg-slate-800/30 rounded-xl p-6 border border-slate-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 bg-gradient-to-br ${color} rounded-lg`}>
            {icon}
          </div>
          <div>
            <h3 className="font-bold text-white flex items-center gap-2">
              {label}
              {isWinner && (
                <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded-full border border-green-500/30">
                  WINNER
                </span>
              )}
            </h3>
            {result && (
              <p className="text-sm text-slate-400">
                {(result.totalTime / 1000).toFixed(2)}s total
              </p>
            )}
          </div>
        </div>
        {result && (
          <div className="text-right">
            <div className="text-sm text-slate-400">Throughput</div>
            <div className="text-lg font-bold text-white">{result.tokensPerSecond} tok/s</div>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="relative h-3 bg-slate-700 rounded-full overflow-hidden mb-4">
        <motion.div
          className={`absolute inset-y-0 left-0 bg-gradient-to-r ${color} rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* Stages */}
      <div className="space-y-2">
        {result?.stages.map((stage, idx) => (
          <div key={idx} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              {stage.status === 'complete' ? (
                <CheckCircle2 className="w-4 h-4 text-green-400" />
              ) : stage.status === 'running' ? (
                <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
              ) : (
                <div className="w-4 h-4 rounded-full border-2 border-slate-600" />
              )}
              <span className="text-slate-300">{stage.name}</span>
            </div>
            <span className="text-slate-400">{stage.duration}ms</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}

function MetricCard({ icon, label, value, color }: MetricCardProps) {
  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center gap-2 mb-2 text-slate-400">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>
        {value}
      </div>
    </div>
  );
}
