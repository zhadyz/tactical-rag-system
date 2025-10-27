import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import {
  Sliders,
  Zap,
  DollarSign,
  Download,
  TrendingDown,
  FileText,
  Layers,
  Hash,
  Cpu
} from 'lucide-react';
import type { BenchmarkConfig, BenchmarkMetrics } from '../../types/demo';
import benchmarkData from '../../data/benchmarks.json';

interface BenchmarkExplorerProps {
  className?: string;
}

export default function BenchmarkExplorer({ className = '' }: BenchmarkExplorerProps) {
  const [config, setConfig] = useState<BenchmarkConfig>({
    documentSize: 500,
    chunkSize: 512,
    topK: 5,
    modelSize: '7B'
  });

  // Interpolate metrics based on config
  const metrics = useMemo(() => {
    return calculateMetrics(config);
  }, [config]);

  const speedup = metrics.cpu.latency / metrics.gpu.latency;
  const costSavings = ((metrics.cpu.costPerMonth - metrics.gpu.costPerMonth) / metrics.cpu.costPerMonth) * 100;
  const monthlyDelta = metrics.cpu.costPerMonth - metrics.gpu.costPerMonth;

  const exportReport = () => {
    const report = {
      timestamp: new Date().toISOString(),
      configuration: config,
      metrics: {
        gpu: metrics.gpu,
        cpu: metrics.cpu
      },
      comparison: {
        speedup: speedup.toFixed(2) + 'x',
        costSavings: costSavings.toFixed(1) + '%',
        monthlyDelta: '$' + monthlyDelta.toFixed(2)
      }
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `apollo-benchmark-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Chart data for latency comparison
  const latencyData = [
    {
      name: 'Latency',
      GPU: metrics.gpu.latency,
      CPU: metrics.cpu.latency
    }
  ];

  // Chart data for cost over time
  const costData = Array.from({ length: 12 }, (_, i) => ({
    month: `M${i + 1}`,
    GPU: (metrics.gpu.costPerMonth * (i + 1)),
    CPU: (metrics.cpu.costPerMonth * (i + 1)),
    Savings: (monthlyDelta * (i + 1))
  }));

  return (
    <div className={`bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 border border-slate-700 ${className}`}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl">
              <Sliders className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Interactive Benchmark Explorer</h2>
              <p className="text-slate-400">Explore performance across different configurations</p>
            </div>
          </div>
          <button
            onClick={exportReport}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4 text-slate-300" />
            <span className="text-sm text-slate-300">Export Report</span>
          </button>
        </div>
      </div>

      {/* Configuration Sliders */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <SliderControl
          icon={<FileText className="w-5 h-5" />}
          label="Document Size"
          value={config.documentSize}
          onChange={(value) => setConfig({ ...config, documentSize: value })}
          min={100}
          max={2000}
          step={100}
          unit="KB"
          color="from-blue-500 to-cyan-500"
        />

        <SliderControl
          icon={<Layers className="w-5 h-5" />}
          label="Chunk Size"
          value={config.chunkSize}
          onChange={(value) => setConfig({ ...config, chunkSize: value })}
          min={256}
          max={2048}
          step={256}
          unit="chars"
          color="from-purple-500 to-pink-500"
        />

        <SliderControl
          icon={<Hash className="w-5 h-5" />}
          label="Top K Results"
          value={config.topK}
          onChange={(value) => setConfig({ ...config, topK: value })}
          min={3}
          max={20}
          step={1}
          unit="results"
          color="from-orange-500 to-red-500"
        />

        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <label className="text-sm font-medium text-slate-300">Model Size</label>
          </div>
          <div className="flex gap-2">
            {(['7B', '13B', '70B'] as const).map((size) => (
              <button
                key={size}
                onClick={() => setConfig({ ...config, modelSize: size })}
                className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-all ${
                  config.modelSize === size
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {size}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <MetricCard
          icon={<Zap className="w-5 h-5" />}
          label="Speedup"
          value={`${speedup.toFixed(2)}x`}
          subValue="faster on GPU"
          color="text-yellow-400"
          bgColor="from-yellow-500/20 to-orange-500/20"
        />

        <MetricCard
          icon={<TrendingDown className="w-5 h-5" />}
          label="Cost Savings"
          value={`${costSavings.toFixed(1)}%`}
          subValue="monthly reduction"
          color="text-green-400"
          bgColor="from-green-500/20 to-emerald-500/20"
        />

        <MetricCard
          icon={<DollarSign className="w-5 h-5" />}
          label="Monthly Delta"
          value={`$${monthlyDelta.toFixed(2)}`}
          subValue="at 10k queries"
          color="text-blue-400"
          bgColor="from-blue-500/20 to-cyan-500/20"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latency Comparison */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-4">Latency Comparison</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" label={{ value: 'ms', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Legend />
              <Bar dataKey="GPU" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
              <Bar dataKey="CPU" fill="#f97316" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Cost Over Time */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-4">Cumulative Cost (12 months)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={costData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" label={{ value: '$', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Legend />
              <Area type="monotone" dataKey="GPU" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
              <Area type="monotone" dataKey="CPU" stackId="2" stroke="#f97316" fill="#f97316" fillOpacity={0.6} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Detailed Metrics */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 lg:col-span-2">
          <h3 className="text-lg font-bold text-white mb-4">Detailed Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <MetricsTable title="GPU Accelerated" metrics={metrics.gpu} color="text-purple-400" />
            <MetricsTable title="CPU Only" metrics={metrics.cpu} color="text-orange-400" />
          </div>
        </div>
      </div>
    </div>
  );
}

interface SliderControlProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  unit: string;
  color: string;
}

function SliderControl({ icon, label, value, onChange, min, max, step, unit, color }: SliderControlProps) {
  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`p-2 bg-gradient-to-br ${color} rounded-lg`}>
            {icon}
          </div>
          <label className="text-sm font-medium text-slate-300">{label}</label>
        </div>
        <span className="text-lg font-bold text-white">
          {value} <span className="text-sm text-slate-400">{unit}</span>
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
      />
      <div className="flex justify-between text-xs text-slate-500 mt-1">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subValue: string;
  color: string;
  bgColor: string;
}

function MetricCard({ icon, label, value, subValue, color, bgColor }: MetricCardProps) {
  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`bg-gradient-to-br ${bgColor} rounded-xl p-6 border border-slate-700`}
    >
      <div className="flex items-center gap-2 mb-3 text-slate-400">
        {icon}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className={`text-3xl font-bold ${color} mb-1`}>
        {value}
      </div>
      <div className="text-sm text-slate-400">
        {subValue}
      </div>
    </motion.div>
  );
}

interface MetricsTableProps {
  title: string;
  metrics: BenchmarkMetrics;
  color: string;
}

function MetricsTable({ title, metrics, color }: MetricsTableProps) {
  const rows = [
    { label: 'Latency', value: `${metrics.latency}ms` },
    { label: 'Throughput', value: `${metrics.throughput} tok/s` },
    { label: 'GPU Utilization', value: `${metrics.gpuUtilization}%` },
    { label: 'Memory Usage', value: `${metrics.memoryUsage}MB` },
    { label: 'Cost/Query', value: `$${metrics.costPerQuery.toFixed(4)}` },
    { label: 'Cost/Month', value: `$${metrics.costPerMonth.toFixed(2)}` }
  ];

  return (
    <div>
      <h4 className={`font-bold ${color} mb-3`}>{title}</h4>
      <div className="space-y-2">
        {rows.map((row, idx) => (
          <div key={idx} className="flex justify-between text-sm">
            <span className="text-slate-400">{row.label}</span>
            <span className="text-white font-medium">{row.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Helper function to calculate metrics based on config
function calculateMetrics(config: BenchmarkConfig): { gpu: BenchmarkMetrics; cpu: BenchmarkMetrics } {
  // Find closest benchmark data point
  const grid = benchmarkData.benchmarkGrid as any[];

  const closest = grid.reduce((prev, curr) => {
    const prevDiff = Math.abs(prev.documentSize - config.documentSize) +
                     Math.abs(prev.chunkSize - config.chunkSize) +
                     Math.abs(prev.topK - config.topK);
    const currDiff = Math.abs(curr.documentSize - config.documentSize) +
                     Math.abs(curr.chunkSize - config.chunkSize) +
                     Math.abs(curr.topK - config.topK);
    return currDiff < prevDiff ? curr : prev;
  });

  // Apply model size scaling
  const modelScaling = config.modelSize === '13B' ? 1.5 : config.modelSize === '70B' ? 4 : 1;

  return {
    gpu: {
      latency: Math.round(closest.gpu.latency * modelScaling),
      throughput: Math.round(closest.gpu.throughput / modelScaling),
      gpuUtilization: Math.min(95, Math.round(closest.gpu.gpuUtilization * modelScaling)),
      memoryUsage: Math.round(closest.gpu.memoryUsage * modelScaling),
      costPerQuery: closest.gpu.costPerQuery * modelScaling,
      costPerMonth: closest.gpu.costPerMonth * modelScaling
    },
    cpu: {
      latency: Math.round(closest.cpu.latency * modelScaling),
      throughput: Math.round(closest.cpu.throughput / modelScaling),
      gpuUtilization: 0,
      memoryUsage: Math.round(closest.cpu.memoryUsage * modelScaling),
      costPerQuery: closest.cpu.costPerQuery * modelScaling,
      costPerMonth: closest.cpu.costPerMonth * modelScaling
    }
  };
}
