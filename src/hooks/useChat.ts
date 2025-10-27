import { useCallback, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import useStore from '../store/useStore';
import { usePerformanceStore } from '../store/performanceStore';
import { api } from '../services/api';
import { useStreamingChat } from './useStreamingChat';
import { useThrottledCallback } from './useThrottledCallback';
import { useConnectionStatus } from './useConnectionStatus';
import type { Message } from '../types';

export const useChat = () => {
  const addMessage = useStore((state) => state.addMessage);
  const appendToLastMessage = useStore((state) => state.appendToLastMessage);
  const updateLastMessage = useStore((state) => state.updateLastMessage);
  const setLastMessageStreaming = useStore((state) => state.setLastMessageStreaming);
  const setLoading = useStore((state) => state.setLoading);
  const setStreaming = useStore((state) => state.setStreaming);
  const setError = useStore((state) => state.setError);
  const settings = useStore((state) => state.settings);
  const { sendMessageStream, cancelStream } = useStreamingChat();
  const addQuery = usePerformanceStore((state) => state.addQuery);
  const { isOnline } = useConnectionStatus();

  // PERFORMANCE OPTIMIZATION: Batch token accumulation
  const tokenBufferRef = useRef<string>('');
  const flushTokens = useCallback(() => {
    if (tokenBufferRef.current) {
      appendToLastMessage(tokenBufferRef.current);
      tokenBufferRef.current = '';
    }
  }, [appendToLastMessage]);

  // PERFORMANCE OPTIMIZATION: Throttle token updates to reduce re-renders
  // Updates happen at most once per frame (~60fps) instead of per token
  const throttledFlushTokens = useThrottledCallback(flushTokens, 16);

  const sendMessage = useCallback(
    async (content: string) => {
      try {
        // Check connection status before sending
        if (!isOnline) {
          const offlineError = 'Cannot send message while offline. Please check your connection.';
          setError(offlineError);

          // Add error message to chat
          const errorMessage: Message = {
            id: uuidv4(),
            role: 'assistant',
            content: offlineError,
            timestamp: new Date(),
          };
          addMessage(errorMessage);
          return;
        }

        // Clear any previous errors
        setError(null);

        // Add user message
        const userMessage: Message = {
          id: uuidv4(),
          role: 'user',
          content,
          timestamp: new Date(),
        };
        addMessage(userMessage);

        // Check if streaming is enabled
        if (settings.streamResponse) {
          // Create placeholder assistant message
          const assistantMessage: Message = {
            id: uuidv4(),
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isStreaming: true,
          };
          addMessage(assistantMessage);

          // Set streaming state
          setStreaming(true);

          // Send streaming request
          await sendMessageStream(
            {
              question: content,
              mode: settings.mode,
              use_context: settings.useContext,
              rerank_preset: settings.rerankPreset,
            },
            {
              onToken: (token: string) => {
                // PERFORMANCE OPTIMIZATION: Buffer tokens and flush throttled
                // This reduces re-renders from 100+ per second to ~60fps max
                tokenBufferRef.current += token;
                throttledFlushTokens();
              },
              onSources: (sources: any[]) => {
                // Flush any pending tokens before updating sources
                flushTokens();
                // Update last message with sources
                updateLastMessage(assistantMessage.content, sources);
              },
              onMetadata: (metadata: any) => {
                // Flush any pending tokens before updating metadata
                flushTokens();
                // Update last message with metadata
                updateLastMessage(assistantMessage.content, undefined, {
                  mode_used: metadata.mode,
                  processing_time: metadata.processing_time_ms,
                  ...metadata,
                });

                // Track performance metrics (streaming)
                if (metadata?.processing_time_ms) {
                  addQuery({
                    id: uuidv4(),
                    timestamp: new Date().toISOString(),
                    question: content,
                    time_ms: metadata.processing_time_ms,
                    cache_hit: metadata.cache_hit || false,
                    breakdown: metadata.timing_breakdown,
                    strategy_used: metadata.strategy_used,
                    query_type: metadata.query_type,
                    mode: metadata.mode,
                  });
                }
              },
              onDone: () => {
                // Flush any remaining tokens before marking complete
                flushTokens();
                // Mark streaming as complete
                setLastMessageStreaming(false);
                setStreaming(false);
              },
              onError: (error: string) => {
                // Flush any remaining tokens before handling error
                flushTokens();
                console.error('Streaming error:', error);
                setError(error);
                setLastMessageStreaming(false);
                setStreaming(false);
              },
            }
          );
        } else {
          // Use traditional non-streaming API
          setLoading(true);

          // Call API
          const response = await api.query({
            question: content,
            mode: settings.mode,
            use_context: settings.useContext,
            rerank_preset: settings.rerankPreset,
          });

          // Add assistant response
          const assistantMessage: Message = {
            id: uuidv4(),
            role: 'assistant',
            content: response.answer,
            sources: response.sources,
            timestamp: new Date(),
            metadata: {
              mode_used: response.mode_used,
              processing_time: response.processing_time,
              ...response.metadata,
            },
          };
          addMessage(assistantMessage);

          // Track performance metrics (non-streaming)
          if (response.metadata?.processing_time_ms) {
            addQuery({
              id: uuidv4(),
              timestamp: new Date().toISOString(),
              question: content,
              time_ms: response.metadata.processing_time_ms,
              cache_hit: response.metadata.cache_hit || false,
              breakdown: response.metadata.timing_breakdown,
              strategy_used: response.metadata.strategy_used,
              query_type: response.metadata.query_type,
              mode: response.metadata.mode,
            });
          }

          setLoading(false);
        }
      } catch (err: any) {
        console.error('Error sending message:', err);
        setError(err.message || 'Failed to send message. Please try again.');

        // Optionally add an error message to the chat
        const errorMessage: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: `I'm sorry, I encountered an error: ${
            err.message || 'Unknown error'
          }`,
          timestamp: new Date(),
        };
        addMessage(errorMessage);

        setLoading(false);
        setStreaming(false);
      }
    },
    [
      addMessage,
      appendToLastMessage,
      updateLastMessage,
      setLastMessageStreaming,
      setLoading,
      setStreaming,
      setError,
      settings,
      sendMessageStream,
      addQuery,
      throttledFlushTokens,
      flushTokens,
      isOnline,
    ]
  );

  return {
    sendMessage,
    cancelStream,
    isOnline,
  };
};
