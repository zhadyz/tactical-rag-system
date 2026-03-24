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

  // Agent store actions
  const addAgentStep = useStore((state) => state.addAgentStep);
  const updateAgentStep = useStore((state) => state.updateAgentStep);
  const setRetrievalStages = useStore((state) => state.setRetrievalStages);
  const setCRAGEvaluations = useStore((state) => state.setCRAGEvaluations);
  const setVerificationResults = useStore((state) => state.setVerificationResults);
  const setAgentActive = useStore((state) => state.setAgentActive);
  const clearAgentState = useStore((state) => state.clearAgentState);
  const finalizeAgentMessage = useStore((state) => state.finalizeAgentMessage);

  // PERFORMANCE OPTIMIZATION: Batch token accumulation
  const tokenBufferRef = useRef<string>('');
  const flushTokens = useCallback(() => {
    if (tokenBufferRef.current) {
      appendToLastMessage(tokenBufferRef.current);
      tokenBufferRef.current = '';
    }
  }, [appendToLastMessage]);

  // PERFORMANCE OPTIMIZATION: Throttle token updates to reduce re-renders
  const throttledFlushTokens = useThrottledCallback(flushTokens, 16);

  const sendMessage = useCallback(
    async (content: string) => {
      try {
        // Check connection status before sending
        if (!isOnline) {
          const offlineError = 'Cannot send message while offline. Please check your connection.';
          setError(offlineError);

          const errorMessage: Message = {
            id: uuidv4(),
            role: 'assistant',
            content: offlineError,
            timestamp: new Date(),
          };
          addMessage(errorMessage);
          return;
        }

        // Clear any previous errors and agent state
        setError(null);
        clearAgentState();

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
                tokenBufferRef.current += token;
                throttledFlushTokens();
              },
              onSources: (sources: any[]) => {
                flushTokens();
                updateLastMessage(assistantMessage.content, sources);
              },
              onMetadata: (metadata: any) => {
                flushTokens();
                updateLastMessage(assistantMessage.content, undefined, {
                  mode_used: metadata.mode,
                  processing_time: metadata.processing_time_ms,
                  ...metadata,
                });

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
                flushTokens();
                finalizeAgentMessage();
                setLastMessageStreaming(false);
                setStreaming(false);
              },
              onError: (error: string) => {
                flushTokens();
                console.error('Streaming error:', error);
                setError(error);
                setLastMessageStreaming(false);
                setStreaming(false);
              },
              onAgentThinking: (thinkingContent: string) => {
                setAgentActive(true);
                addAgentStep({
                  id: uuidv4(),
                  type: 'thinking',
                  timestamp: new Date(),
                  content: thinkingContent,
                  status: 'complete',
                });
              },
              onToolCall: (toolCall: any) => {
                addAgentStep({
                  id: toolCall.id || uuidv4(),
                  type: 'tool_call',
                  timestamp: new Date(),
                  content: `Calling ${toolCall.tool || toolCall.toolName}`,
                  toolName: toolCall.tool || toolCall.toolName,
                  toolInput: toolCall.input,
                  status: 'running',
                });
              },
              onToolResult: (toolResult: any) => {
                const toolCallId = toolResult.tool_call_id || toolResult.toolCallId;
                if (toolCallId) {
                  updateAgentStep(toolCallId, { status: 'complete' });
                }
                addAgentStep({
                  id: uuidv4(),
                  type: 'tool_result',
                  timestamp: new Date(),
                  content: `${toolResult.count || toolResult.resultCount || 0} results in ${toolResult.duration_ms || toolResult.durationMs || 0}ms`,
                  toolName: toolResult.tool || toolResult.toolName,
                  toolOutput: toolResult,
                  durationMs: toolResult.duration_ms || toolResult.durationMs,
                  status: 'complete',
                });
              },
              onCRAGEvaluation: (evaluations: any) => {
                setCRAGEvaluations(evaluations);
                addAgentStep({
                  id: uuidv4(),
                  type: 'crag_evaluation',
                  timestamp: new Date(),
                  content: `Evaluated ${evaluations.length} documents`,
                  status: 'complete',
                });
              },
              onRetrievalComplete: (data: any) => {
                setRetrievalStages(data.stages || []);
                setAgentActive(false);
              },
              onVerification: (results: any) => {
                setVerificationResults(results);
              },
            }
          );
        } else {
          // Use traditional non-streaming API
          setLoading(true);

          const response = await api.query({
            question: content,
            mode: settings.mode,
            use_context: settings.useContext,
            rerank_preset: settings.rerankPreset,
          });

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
      addAgentStep,
      updateAgentStep,
      setRetrievalStages,
      setCRAGEvaluations,
      setVerificationResults,
      setAgentActive,
      clearAgentState,
      finalizeAgentMessage,
    ]
  );

  return {
    sendMessage,
    cancelStream,
    isOnline,
  };
};
