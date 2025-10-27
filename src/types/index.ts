export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
  metadata?: Record<string, any>;
  isStreaming?: boolean;
}

export interface Source {
  content: string;
  // Backend may send content in different field names
  excerpt?: string;
  page_content?: string;
  file_name?: string;
  // Relevance score may be at different levels
  relevance_score?: number;
  metadata: {
    source: string;
    page?: number;
    score: number;
    filePath?: string;
  };
}

export interface QueryRequest {
  question: string;
  mode: 'simple' | 'adaptive';
  use_context: boolean;
  rerank_preset?: 'quick' | 'quality' | 'deep';
}

export interface TimingStage {
  time_ms: number;
  percentage: number;
}

export interface TimingBreakdown {
  total_ms: number;
  stages: Record<string, TimingStage>;
  unaccounted_ms: number;
  unaccounted_percentage: number;
}

export interface QueryMetadata {
  strategy_used: string;
  query_type: string;
  mode: string;
  processing_time_ms: number;
  timing_breakdown?: TimingBreakdown;
  cache_hit?: boolean;
  optimization?: string;
  confidence?: number;
  confidence_interpretation?: string;
  confidence_signals?: Record<string, number>;
}

export interface QueryResponse {
  answer: string;
  sources?: Source[];
  mode_used?: string;
  processing_time?: number;
  metadata?: QueryMetadata;
  explanation?: any;
  error?: boolean;
}

export interface Settings {
  mode: 'simple' | 'adaptive';
  useContext: boolean;
  streamResponse: boolean;
  darkMode: boolean;
  rerankPreset: 'quick' | 'quality' | 'deep';
}

export interface StreamEvent {
  type: 'token' | 'sources' | 'metadata' | 'done' | 'error';
  content?: any;
}

export interface StreamCallbacks {
  onToken?: (token: string) => void;
  onSources?: (sources: Source[]) => void;
  onMetadata?: (metadata: QueryMetadata) => void;
  onDone?: () => void;
  onError?: (error: string) => void;
}

export interface Document {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  status: 'uploading' | 'processing' | 'ready' | 'error';
}

export interface DocumentInfo {
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  file_hash: string;
  num_chunks: number;
  processing_date: string;
}

export interface DocumentListResponse {
  total_documents: number;
  total_chunks: number;
  documents: DocumentInfo[];
}

export interface ReindexResponse {
  success: boolean;
  message: string;
  total_files: number;
  total_chunks: number;
  processing_time_seconds: number;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  version?: string;
  uptime?: number;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}
