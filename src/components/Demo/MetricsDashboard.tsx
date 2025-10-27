import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import {
  Activity,
  Zap,
  Clock,
  Database,
  Cpu,
  TrendingUp,
  Users,
  AlertTriangle
} from 'lucide-react';
import type { RealtimeMetrics, PerformanceAlert } from '../../types/demo';

interface MetricsDashboardProps {
  className?: string;
}

export default function MetricsDashboard({ className = '' }: MetricsDashboardProps) {
  const [metrics, setMetrics] = useState<RealtimeMetrics[]>([]);
  const [currentMetrics, setCurrentMetrics] = useState<RealtimeMetrics>(generateMetrics());
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [isLive, setIsLive] = useState(true);

  const maxDataPoints = 30;

  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      const newMetrics = generateMetrics();
      setCurrentMetrics(newMetrics);

      setMetrics((prev) => {
        const updated = [...prev, newMetrics].slice(-maxDataPoints);
        return updated;
      });

      // Generate alerts for anomalies
      if (newMetrics.queryLatency > 3000) {
        addAlert('warning', 'High query latency detected', 'queryLatency', 3000, newMetrics.queryLatency);
      }
      if (newMetrics.gpuUtilization > 90) {
        addAlert('warning', 'GPU utilization very high', 'gpuUtilization', 90, newMetrics.gpuUtilization);
      }
      if (newMetrics.cacheHitRate < 30) {
        addAlert('info', 'Low cache hit rate', 'cacheHitRate', 30, newMetrics.cacheHitRate);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isLive]);

  const addAlert = (type: 'warning' | 'error' | 'info', message: string, metric: string, threshold: number, value: number) => {
    const alert: PerformanceAlert = {
      id: `alert-${Date.now()}`,
      type,
      message,
      timestamp: Date.now(),
      metric,
      threshold,
      value
    };

    setAlerts((prev) => {
      const filtered = prev.filter(a => Date.now() - a.timestamp < 30000); // Keep alerts for 30s
      return [...filtered, alert].slice(-5); // Max 5 alerts
    });
  };

  const chartData = metrics.map((m, idx) => ({
    time: idx,
    latency: m.queryLatency,
    throughput: m.tokenThroughput,
    cacheHit: m.cacheHitRate,
    gpu: m.gpuUtilization
  }));

  return (
    <div className={`bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 border border-slate-700 ${className}`}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-emerald-500 to-green-500 rounded-xl">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Performance Metrics Dashboard</h2>
              <p className="text-slate-400">Real-time system monitoring</p>
            </div>
          </div>
          <button
            onClick={() => setIsLive(!isLive)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all ${
              isLive
                ? 'bg-green-600 hover:bg-green-500 text-white'
                : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
            }`}
          >
            <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-white animate-pulse' : 'bg-slate-400'}`} />
            {isLive ? 'Live' : 'Paused'}
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <AnimatedMetricCard
          icon={<Clock className="w-5 h-5" />}
          label="Query Latency"
          value={currentMetrics.queryLatency}
          unit="ms"
          color="text-blue-400"
          bgColor="from-blue-500/20 to-cyan-500/20"
          trend={calculateTrend(metrics.map(m => m.queryLatency))}
        />

        <AnimatedMetricCard
          icon={<Zap className="w-5 h-5" />}
          label="Throughput"
          value={currentMetrics.tokenThroughput}
          unit="tok/s"
          color="text-purple-400"
          bgColor="from-purple-500/20 to-pink-500/20"
          trend={calculateTrend(metrics.map(m => m.tokenThroughput))}
        />

        <AnimatedMetricCard
          icon={<Database className="w-5 h-5" />}
          label="Cache Hit Rate"
          value={currentMetrics.cacheHitRate}
          unit="%"
          color="text-green-400"
          bgColor="from-green-500/20 to-emerald-500/20"
          trend={calculateTrend(metrics.map(m => m.cacheHitRate))}
        />

        <AnimatedMetricCard
          icon={<Cpu className="w-5 h-5" />}
          label="GPU Utilization"
          value={currentMetrics.gpuUtilization}
          unit="%"
          color="text-orange-400"
          bgColor="from-orange-500/20 to-red-500/20"
          trend={calculateTrend(metrics.map(m => m.gpuUtilization))}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Latency Chart */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-4">Query Latency</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#94a3b8" hide />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Line
                type="monotone"
                dataKey="latency"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Throughput Chart */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-4">Token Throughput</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#94a3b8" hide />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Area
                type="monotone"
                dataKey="throughput"
                stroke="#8b5cf6"
                fill="#8b5cf6"
                fillOpacity={0.3}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Cache Hit Rate Chart */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-4">Cache Hit Rate</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#94a3b8" hide />
              <YAxis stroke="#94a3b8" domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Line
                type="monotone"
                dataKey="cacheHit"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* GPU Utilization Chart */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-4">GPU Utilization</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#94a3b8" hide />
              <YAxis stroke="#94a3b8" domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Area
                type="monotone"
                dataKey="gpu"
                stroke="#f97316"
                fill="#f97316"
                fillOpacity={0.3}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricBox
          label="GPU Memory"
          value={`${currentMetrics.gpuMemory}MB`}
          color="text-orange-400"
        />
        <MetricBox
          label="CPU Usage"
          value={`${currentMetrics.cpuUtilization}%`}
          color="text-blue-400"
        />
        <MetricBox
          label="RAM Usage"
          value={`${currentMetrics.ramUsage}MB`}
          color="text-purple-400"
        />
        <MetricBox
          label="Active Connections"
          value={currentMetrics.activeConnections.toString()}
          color="text-green-400"
        />
      </div>

      {/* Alerts */}
      <AnimatePresence>
        {alerts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-slate-800/50 rounded-xl p-4 border border-slate-700"
          >
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
              <h3 className="font-bold text-white">Performance Alerts</h3>
            </div>
            <div className="space-y-2">
              {alerts.map((alert) => (
                <AlertCard key={alert.id} alert={alert} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface AnimatedMetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  unit: string;
  color: string;
  bgColor: string;
  trend?: 'up' | 'down' | 'neutral';
}

function AnimatedMetricCard({ icon, label, value, unit, color, bgColor, trend }: AnimatedMetricCardProps) {
  return (
    <motion.div
      initial={{ scale: 0.95 }}
      animate={{ scale: 1 }}
      className={`bg-gradient-to-br ${bgColor} rounded-xl p-4 border border-slate-700`}
    >
      <div className="flex items-center gap-2 mb-2 text-slate-400">
        {icon}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <motion.div
        key={value}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`text-3xl font-bold ${color} flex items-baseline gap-1`}
      >
        <span>{value}</span>
        <span className="text-lg">{unit}</span>
      </motion.div>
      {trend && (
        <div className={`text-xs mt-1 ${
          trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-slate-400'
        }`}>
          {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} vs previous
        </div>
      )}
    </motion.div>
  );
}

interface MetricBoxProps {
  label: string;
  value: string;
  color: string;
}

function MetricBox({ label, value, color }: MetricBoxProps) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`text-xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

interface AlertCardProps {
  alert: PerformanceAlert;
}

function AlertCard({ alert }: AlertCardProps) {
  const bgColor = alert.type === 'error' ? 'bg-red-500/10' : alert.type === 'warning' ? 'bg-yellow-500/10' : 'bg-blue-500/10';
  const borderColor = alert.type === 'error' ? 'border-red-500/30' : alert.type === 'warning' ? 'border-yellow-500/30' : 'border-blue-500/30';
  const textColor = alert.type === 'error' ? 'text-red-400' : alert.type === 'warning' ? 'text-yellow-400' : 'text-blue-400';

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className={`${bgColor} rounded-lg p-3 border ${borderColor}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className={`text-sm font-semibold ${textColor} mb-1`}>{alert.message}</div>
          <div className="text-xs text-slate-400">
            {alert.metric}: {alert.value} (threshold: {alert.threshold})
          </div>
        </div>
        <span className="text-xs text-slate-500">
          {Math.floor((Date.now() - alert.timestamp) / 1000)}s ago
        </span>
      </div>
    </motion.div>
  );
}

// Helper functions
function generateMetrics(): RealtimeMetrics {
  return {
    timestamp: Date.now(),
    queryLatency: 1400 + Math.random() * 800,
    tokenThroughput: 70 + Math.random() * 30,
    cacheHitRate: 40 + Math.random() * 50,
    gpuUtilization: 60 + Math.random() * 30,
    gpuMemory: 6000 + Math.random() * 2000,
    cpuUtilization: 30 + Math.random() * 40,
    ramUsage: 8000 + Math.random() * 2000,
    activeConnections: Math.floor(10 + Math.random() * 20)
  };
}

function calculateTrend(values: number[]): 'up' | 'down' | 'neutral' {
  if (values.length < 2) return 'neutral';
  const recent = values.slice(-5);
  const avg = recent.reduce((a, b) => a + b, 0) / recent.length;
  const prev = recent[0];
  const diff = avg - prev;
  if (Math.abs(diff) < prev * 0.05) return 'neutral';
  return diff > 0 ? 'up' : 'down';
}
