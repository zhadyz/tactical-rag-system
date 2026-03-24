// Agent tool names
export type AgentToolName =
  | 'semantic_search'
  | 'proposition_search'
  | 'keyword_search'
  | 'graph_traverse'
  | 'chunk_read'
  | 'section_read'
  | string;

export interface AgentStep {
  id: string;
  type: 'thinking' | 'tool_call' | 'tool_result' | 'crag_evaluation' | 'verification';
  timestamp: Date;
  content: string;
  toolName?: AgentToolName;
  toolInput?: Record<string, any>;
  toolOutput?: any;
  durationMs?: number;
  status: 'pending' | 'running' | 'complete' | 'error';
}

export interface ToolCall {
  id: string;
  toolName: AgentToolName;
  input: Record<string, any>;
  timestamp: Date;
}

export interface ToolResult {
  id: string;
  toolCallId: string;
  toolName: AgentToolName;
  output: any;
  durationMs: number;
  resultCount?: number;
}

export interface CRAGEvaluation {
  documentId: string;
  source: string;
  score: number;
  verdict: 'correct' | 'incorrect' | 'ambiguous';
  reason?: string;
}

export interface VerificationResult {
  claim: string;
  supported: boolean;
  confidence: number;
  supportingSources: string[];
  explanation?: string;
}

export interface RetrievalStage {
  stageName: string;
  resultsCount: number;
  topScore: number;
  durationMs: number;
  sources: Source[];
}

export interface IngestStatusResponse {
  status: 'idle' | 'running' | 'complete' | 'error';
  progress: number;
  currentStage?: string;
  documentsProcessed?: number;
  totalDocuments?: number;
  error?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
  metadata?: Record<string, any>;
  isStreaming?: boolean;
  agentSteps?: AgentStep[];
  retrievalStages?: RetrievalStage[];
  cragEvaluations?: CRAGEvaluation[];
  verificationResults?: VerificationResult[];
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
  mode: 'direct' | 'agentic';
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
  mode: 'direct' | 'agentic';
  useContext: boolean;
  streamResponse: boolean;
  darkMode: boolean;
  rerankPreset: 'quick' | 'quality' | 'deep';
  showAgentReasoning: boolean;
}

export interface StreamEvent {
  type: 'token' | 'sources' | 'metadata' | 'done' | 'error'
    | 'agent_thinking' | 'tool_call' | 'tool_result' | 'crag_evaluation' | 'retrieval_complete' | 'verification';
  content?: any;
}

export interface StreamCallbacks {
  onToken?: (token: string) => void;
  onSources?: (sources: Source[]) => void;
  onMetadata?: (metadata: QueryMetadata) => void;
  onDone?: () => void;
  onError?: (error: string) => void;
  onAgentThinking?: (content: string) => void;
  onToolCall?: (toolCall: any) => void;
  onToolResult?: (toolResult: any) => void;
  onCRAGEvaluation?: (evaluations: CRAGEvaluation[]) => void;
  onRetrievalComplete?: (data: any) => void;
  onVerification?: (results: VerificationResult[]) => void;
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
