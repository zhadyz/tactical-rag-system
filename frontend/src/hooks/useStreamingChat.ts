import { useRef, useCallback } from 'react';
import type { QueryRequest, StreamEvent, StreamCallbacks } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const useStreamingChat = () => {
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessageStream = useCallback(
    async (request: QueryRequest, callbacks: StreamCallbacks) => {
      // Cancel any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();

      try {
        const response = await fetch(`${API_BASE}/api/query/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({
            message: `HTTP ${response.status}`,
          }));
          throw new Error(errorData.message || `HTTP ${response.status}`);
        }

        if (!response.body) {
          throw new Error('Response body is null');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          // Decode the chunk
          buffer += decoder.decode(value, { stream: true });

          // Split by newlines to process complete lines
          const lines = buffer.split('\n');

          // Keep the last incomplete line in the buffer
          buffer = lines.pop() || '';

          // Process each complete line
          for (const line of lines) {
            // SSE format: "data: {json}"
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.slice(6); // Remove "data: " prefix
                const event: StreamEvent = JSON.parse(jsonStr);

                // Handle different event types
                switch (event.type) {
                  case 'token':
                    if (callbacks.onToken && event.content) {
                      callbacks.onToken(event.content);
                    }
                    break;

                  case 'sources':
                    if (callbacks.onSources && event.content) {
                      callbacks.onSources(event.content);
                    }
                    break;

                  case 'metadata':
                    if (callbacks.onMetadata && event.content) {
                      callbacks.onMetadata(event.content);
                    }
                    break;

                  case 'done':
                    if (callbacks.onDone) {
                      callbacks.onDone();
                    }
                    break;

                  case 'error':
                    if (callbacks.onError && event.content) {
                      callbacks.onError(event.content);
                    }
                    break;

                  default:
                    if (import.meta.env.DEV) {
                      console.warn('Unknown event type:', event.type);
                    }
                }
              } catch (err) {
                if (import.meta.env.DEV) {
                  console.error('Error parsing SSE event:', err, line);
                }
              }
            }
          }
        }

        // Process any remaining buffer
        if (buffer.trim().startsWith('data: ')) {
          try {
            const jsonStr = buffer.trim().slice(6);
            const event: StreamEvent = JSON.parse(jsonStr);

            if (event.type === 'done' && callbacks.onDone) {
              callbacks.onDone();
            }
          } catch (err) {
            if (import.meta.env.DEV) {
              console.error('Error parsing final SSE event:', err);
            }
          }
        }

      } catch (err: any) {
        // Don't report errors for aborted requests
        if (err.name === 'AbortError') {
          if (import.meta.env.DEV) {
            console.log('Stream aborted by user');
          }
          return;
        }

        if (import.meta.env.DEV) {
          console.error('Streaming error:', err);
        }
        if (callbacks.onError) {
          callbacks.onError(err.message || 'Stream failed');
        }
      } finally {
        abortControllerRef.current = null;
      }
    },
    []
  );

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  const isStreaming = useCallback(() => {
    return abortControllerRef.current !== null;
  }, []);

  return {
    sendMessageStream,
    cancelStream,
    isStreaming,
  };
};
