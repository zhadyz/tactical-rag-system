import type { QueryRequest, QueryResponse, HealthStatus, DocumentListResponse, ReindexResponse } from '../types';
import { API } from '../constants/ui';

// Tauri desktop app: Connect directly to backend (no proxy needed)
// Development: Docker backend at localhost:8000
// Production: Sidecar backend at 127.0.0.1:8000
const API_BASE = import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? 'http://localhost:8000' : 'http://127.0.0.1:8000');

class ApiError extends Error {
  status?: number;
  code?: string;
  isNetworkError?: boolean;

  constructor(
    message: string,
    status?: number,
    code?: string,
    isNetworkError = false
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.isNetworkError = isNetworkError;
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

  const data = await response.json();

  // Validate structure
  if (!data || typeof data !== 'object') {
    throw new ApiError('Invalid response format');
  }

  return data as T;
}

// Helper function for fetch with timeout
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs = 30000
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw new ApiError('Request timeout', 408, 'TIMEOUT', true);
    }
    // Mark as network error if it's a fetch failure
    if (err.message?.toLowerCase().includes('failed to fetch') ||
        err.message?.toLowerCase().includes('network')) {
      throw new ApiError(err.message || 'Network error', undefined, 'NETWORK_ERROR', true);
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

// Retry helper with exponential backoff
// Only retries network errors, not HTTP 4xx/5xx errors
async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  maxRetries = API.MAX_RETRIES
): Promise<T> {
  let lastError: any;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      lastError = err;
      const isLastAttempt = attempt === maxRetries - 1;

      // Don't retry if it's not a network error
      // Don't retry 4xx/5xx HTTP errors - those are client/server errors
      const isNetworkError = err.isNetworkError ||
                             err.name === 'AbortError' ||
                             err.message?.toLowerCase().includes('network') ||
                             err.message?.toLowerCase().includes('timeout') ||
                             err.message?.toLowerCase().includes('failed to fetch');

      const isHttpError = err.status && err.status >= 400;

      // Only retry on network errors, not HTTP errors
      if (isLastAttempt || !isNetworkError || isHttpError) {
        throw err;
      }

      // Exponential backoff: 1s, 2s, 4s
      const delay = Math.pow(2, attempt) * API.RETRY_DELAY_BASE;
      console.log(`Network error on attempt ${attempt + 1}/${maxRetries}. Retrying in ${delay}ms...`, err.message);

      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

export const api = {
  // Query endpoint with retry logic
  query: async (request: QueryRequest): Promise<QueryResponse> => {
    return fetchWithRetry(async () => {
      const response = await fetchWithTimeout(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      }, API.QUERY_TIMEOUT);
      return handleResponse<QueryResponse>(response);
    });
  },

  // Health check - no retry (fast fail for status checks)
  health: async (): Promise<HealthStatus> => {
    const response = await fetchWithTimeout(`${API_BASE}/api/health`, {}, API.HEALTH_CHECK_TIMEOUT);
    return handleResponse<HealthStatus>(response);
  },

  // Document upload with retry
  uploadDocument: async (file: File): Promise<any> => {
    return fetchWithRetry(async () => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetchWithTimeout(`${API_BASE}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      }, API.DEFAULT_TIMEOUT);
      return handleResponse<any>(response);
    });
  },

  // List documents with retry
  listDocuments: async (): Promise<DocumentListResponse> => {
    return fetchWithRetry(async () => {
      const response = await fetchWithTimeout(`${API_BASE}/api/documents`, {}, API.DEFAULT_TIMEOUT);
      return handleResponse<DocumentListResponse>(response);
    });
  },

  // Reindex documents with retry
  reindexDocuments: async (): Promise<ReindexResponse> => {
    return fetchWithRetry(async () => {
      const response = await fetchWithTimeout(`${API_BASE}/api/documents/reindex`, {
        method: 'POST',
      }, API.DEFAULT_TIMEOUT);
      return handleResponse<ReindexResponse>(response);
    });
  },

  // Delete document with retry
  deleteDocument: async (id: string): Promise<void> => {
    return fetchWithRetry(async () => {
      const response = await fetchWithTimeout(`${API_BASE}/api/documents/${id}`, {
        method: 'DELETE',
      }, API.DEFAULT_TIMEOUT);
      if (!response.ok) {
        throw new ApiError(`Failed to delete document`, response.status);
      }
    });
  },

  // Get conversation history with retry
  getConversation: async (conversationId: string): Promise<any> => {
    return fetchWithRetry(async () => {
      const response = await fetchWithTimeout(
        `${API_BASE}/api/conversations/${conversationId}`,
        {},
        API.DEFAULT_TIMEOUT
      );
      return handleResponse<any>(response);
    });
  },

  // Clear conversation with retry
  clearConversation: async (conversationId: string): Promise<void> => {
    return fetchWithRetry(async () => {
      const response = await fetchWithTimeout(
        `${API_BASE}/api/conversations/${conversationId}`,
        { method: 'DELETE' },
        API.DEFAULT_TIMEOUT
      );
      if (!response.ok) {
        throw new ApiError(`Failed to clear conversation`, response.status);
      }
    });
  },

  // Clear cache and conversation memory with retry
  clearCacheAndMemory: async (): Promise<{ success: boolean; message: string }> => {
    return fetchWithRetry(async () => {
      const response = await fetchWithTimeout(`${API_BASE}/api/conversation/clear`, {
        method: 'POST',
      }, API.DEFAULT_TIMEOUT);
      return handleResponse<{ success: boolean; message: string }>(response);
    });
  },

  // Get settings with retry
  getSettings: async (): Promise<{ success: boolean; message: string; current_settings: any }> => {
    return fetchWithRetry(async () => {
      const response = await fetchWithTimeout(`${API_BASE}/api/settings`, {}, API.DEFAULT_TIMEOUT);
      return handleResponse<{ success: boolean; message: string; current_settings: any }>(response);
    });
  },

  // Update settings (including model hot-swap) with retry
  updateSettings: async (settings: any): Promise<{ success: boolean; message: string; current_settings: any }> => {
    return fetchWithRetry(async () => {
      const response = await fetchWithTimeout(`${API_BASE}/api/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      }, API.DEFAULT_TIMEOUT);
      return handleResponse<{ success: boolean; message: string; current_settings: any }>(response);
    });
  },
};

export { ApiError };
