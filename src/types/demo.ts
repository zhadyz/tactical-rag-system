/**
 * Type definitions for interactive demonstration components
 */

// ==================== Performance Race ====================

export interface RaceResult {
  pipeline: 'gpu' | 'cpu';
  stages: RaceStage[];
  totalTime: number;
  tokensPerSecond: number;
  memoryUsage: number;
}

export interface RaceStage {
  name: string;
  startTime: number;
  endTime: number;
  duration: number;
  status: 'pending' | 'running' | 'complete' | 'error';
}

export interface RaceDocument {
  name: string;
  size: number;
  chunks: number;
  content?: string;
}

export interface RaceConfig {
  document: RaceDocument;
  query: string;
  modelSize: '7B' | '13B' | '70B';
  chunkSize: number;
  topK: number;
}

// ==================== Benchmark Explorer ====================

export interface BenchmarkConfig {
  documentSize: number;      // KB
  chunkSize: number;          // characters
  topK: number;              // number of results
  modelSize: '7B' | '13B' | '70B';
}

export interface BenchmarkMetrics {
  latency: number;           // ms
  throughput: number;        // tokens/sec
  gpuUtilization: number;    // percentage
  memoryUsage: number;       // MB
  costPerQuery: number;      // USD
  costPerMonth: number;      // USD (at 10k queries)
}

export interface BenchmarkDataPoint {
  config: BenchmarkConfig;
  gpu: BenchmarkMetrics;
  cpu: BenchmarkMetrics;
}

export interface BenchmarkComparison {
  speedup: number;           // multiplier
  costSavings: number;       // percentage
  monthlyDelta: number;      // USD
}

// ==================== RAG Pipeline ====================

export interface PipelineStep {
  id: string;
  name: string;
  description: string;
  timing: {
    gpu: number;             // ms
    cpu: number;             // ms
  };
  details: PipelineStepDetails;
  status: 'pending' | 'running' | 'complete';
  progress?: number;         // 0-100
}

export interface PipelineStepDetails {
  input: string;
  output: string;
  metrics?: Record<string, number>;
  explanation?: string;
}

export interface RAGPipelineData {
  steps: PipelineStep[];
  totalTiming: {
    gpu: number;
    cpu: number;
  };
  document: {
    name: string;
    size: number;
    chunks: number;
  };
  query: string;
  answer: string;
}

// ==================== Code Playground ====================

export interface CodeExample {
  id: string;
  name: string;
  description: string;
  framework: 'python' | 'nodejs' | 'curl';
  code: string;
  response?: string;
  tags: string[];
}

export interface PlaygroundState {
  activeFramework: 'python' | 'nodejs' | 'curl';
  activeExample: string;
  customCode?: string;
  output?: string;
  isRunning: boolean;
}

// ==================== Embedding Visualizer ====================

export interface EmbeddingPoint {
  id: string;
  position: [number, number, number]; // 3D coordinates
  text: string;
  source: string;
  similarity: number;
  metadata?: Record<string, any>;
}

export interface EmbeddingSpace {
  points: EmbeddingPoint[];
  queryPoint?: EmbeddingPoint;
  similarityThreshold: number;
  colorScheme: 'source' | 'similarity' | 'cluster';
}

export interface EmbeddingQuery {
  text: string;
  topK: number;
  minSimilarity: number;
}

// ==================== Metrics Dashboard ====================

export interface RealtimeMetrics {
  timestamp: number;
  queryLatency: number;        // ms
  tokenThroughput: number;     // tokens/sec
  cacheHitRate: number;        // percentage
  gpuUtilization: number;      // percentage
  gpuMemory: number;           // MB
  cpuUtilization: number;      // percentage
  ramUsage: number;            // MB
  activeConnections: number;
}

export interface MetricsHistory {
  metrics: RealtimeMetrics[];
  windowSize: number;          // number of data points to keep
  updateInterval: number;      // ms
}

export interface PerformanceAlert {
  id: string;
  type: 'warning' | 'error' | 'info';
  message: string;
  timestamp: number;
  metric: string;
  threshold: number;
  value: number;
}

// ==================== Sample Data ====================

export interface SampleDocument {
  id: string;
  name: string;
  description: string;
  size: number;
  chunks: number;
  content: string;
  category: 'technical' | 'medical' | 'legal' | 'general';
}

// ==================== Export Report ====================

export interface ExportConfig {
  format: 'png' | 'pdf' | 'json';
  includeRawData: boolean;
  timestamp: boolean;
  watermark?: string;
}

export interface ExportableData {
  title: string;
  subtitle?: string;
  data: any;
  metadata: Record<string, any>;
  timestamp: number;
}
