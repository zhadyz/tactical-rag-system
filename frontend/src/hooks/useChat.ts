import { useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import useStore from '../store/useStore';
// Temporarily disable performanceStore to debug Suspense error
// import { usePerformanceStore } from '../store/performanceStore';
import { api } from '../services/api';
import { useStreamingChat } from './useStreamingChat';
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
  // const addQuery = usePerformanceStore((state) => state.addQuery);

  const sendMessage = useCallback(
    async (content: string) => {
      try {
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
            },
            {
              onToken: (token: string) => {
                // Append token to the last message
                appendToLastMessage(token);
              },
              onSources: (sources: any[]) => {
                // Update last message with sources
                updateLastMessage(assistantMessage.content, sources);
              },
              onMetadata: (metadata: any) => {
                // Update last message with metadata
                updateLastMessage(assistantMessage.content, undefined, {
                  mode_used: metadata.mode,
                  processing_time: metadata.processing_time_ms,
                  ...metadata,
                });
              },
              onDone: () => {
                // Mark streaming as complete
                setLastMessageStreaming(false);
                setStreaming(false);
              },
              onError: (error: string) => {
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

          setLoading(false);
        }

        // Track performance metrics - Temporarily disabled to debug Suspense error
        // if (response.metadata?.processing_time_ms) {
        //   addQuery({
        //     id: uuidv4(),
        //     timestamp: new Date().toISOString(),
        //     question: content,
        //     time_ms: response.metadata.processing_time_ms,
        //     cache_hit: response.metadata.cache_hit || false,
        //     breakdown: response.metadata.timing_breakdown,
        //     strategy_used: response.metadata.strategy_used,
        //     query_type: response.metadata.query_type,
        //     mode: response.metadata.mode,
        //   });
        // }
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
    ]
  );

  return {
    sendMessage,
    cancelStream,
  };
};
