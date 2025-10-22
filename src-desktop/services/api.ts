import type { QueryRequest, QueryResponse, HealthStatus, DocumentListResponse, ReindexResponse } from '../types';

// Tauri desktop app: Connect directly to backend (no proxy needed)
// Development: Docker backend at localhost:8000
// Production: Sidecar backend at 127.0.0.1:8000
const API_BASE = import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? 'http://localhost:8000' : 'http://127.0.0.1:8000');

class ApiError extends Error {
  status?: number;
  code?: string;

  constructor(
    message: string,
    status?: number,
    code?: string
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({
      message: 'An unknown error occurred',
    }));
    throw new ApiError(
      error.message || `HTTP ${response.status}`,
      response.status,
      error.code
    );
  }
  return response.json();
}

export const api = {
  // Query endpoint
  query: async (request: QueryRequest): Promise<QueryResponse> => {
    const response = await fetch(`${API_BASE}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<QueryResponse>(response);
  },

  // Health check
  health: async (): Promise<HealthStatus> => {
    const response = await fetch(`${API_BASE}/api/health`);
    return handleResponse<HealthStatus>(response);
  },

  // Document upload
  uploadDocument: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<any>(response);
  },

  // List documents
  listDocuments: async (): Promise<DocumentListResponse> => {
    const response = await fetch(`${API_BASE}/api/documents`);
    return handleResponse<DocumentListResponse>(response);
  },

  // Reindex documents
  reindexDocuments: async (): Promise<ReindexResponse> => {
    const response = await fetch(`${API_BASE}/api/documents/reindex`, {
      method: 'POST',
    });
    return handleResponse<ReindexResponse>(response);
  },

  // Delete document
  deleteDocument: async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/api/documents/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new ApiError(`Failed to delete document`, response.status);
    }
  },

  // Get conversation history
  getConversation: async (conversationId: string): Promise<any> => {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`
    );
    return handleResponse<any>(response);
  },

  // Clear conversation
  clearConversation: async (conversationId: string): Promise<void> => {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`,
      {
        method: 'DELETE',
      }
    );
    if (!response.ok) {
      throw new ApiError(`Failed to clear conversation`, response.status);
    }
  },

  // Clear cache and conversation memory
  clearCacheAndMemory: async (): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE}/api/conversation/clear`, {
      method: 'POST',
    });
    return handleResponse<{ success: boolean; message: string }>(response);
  },

  // Get settings
  getSettings: async (): Promise<{ success: boolean; message: string; current_settings: any }> => {
    const response = await fetch(`${API_BASE}/api/settings`);
    return handleResponse<{ success: boolean; message: string; current_settings: any }>(response);
  },

  // Update settings (including model hot-swap)
  updateSettings: async (settings: any): Promise<{ success: boolean; message: string; current_settings: any }> => {
    const response = await fetch(`${API_BASE}/api/settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
    return handleResponse<{ success: boolean; message: string; current_settings: any }>(response);
  },
};

export { ApiError };
