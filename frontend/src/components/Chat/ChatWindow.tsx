import React, { useEffect, useRef } from 'react';
import { AlertCircle } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import useStore from '../../store/useStore';
import { useChat } from '../../hooks/useChat';

export const ChatWindow: React.FC = () => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messages = useStore((state) => state.messages);
  const isLoading = useStore((state) => state.isLoading);
  const isStreaming = useStore((state) => state.isStreaming);
  const error = useStore((state) => state.error);

  const { sendMessage, cancelStream } = useChat();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Messages container */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          // Empty state
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md px-4">
              <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-primary-600 dark:text-primary-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                Welcome to Tactical RAG
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Ask questions about your documents and get intelligent,
                context-aware answers powered by advanced retrieval and
                reasoning.
              </p>
              <div className="text-sm text-gray-500 dark:text-gray-400 space-y-2">
                <p>Try asking:</p>
                <ul className="text-left space-y-1 max-w-xs mx-auto">
                  <li className="flex items-start gap-2">
                    <span className="text-primary-600 dark:text-primary-400">•</span>
                    <span>What are the main topics in the documents?</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary-600 dark:text-primary-400">•</span>
                    <span>Summarize the key findings</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary-600 dark:text-primary-400">•</span>
                    <span>Compare different sections</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          // Messages list
          <div className="max-w-4xl mx-auto w-full">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="max-w-4xl mx-auto w-full px-6 pb-4">
            <div className="flex items-center gap-3 p-4 bg-error-50 dark:bg-error-900/30 border border-error-200 dark:border-error-800 rounded-lg">
              <AlertCircle
                size={20}
                className="text-error-600 dark:text-error-400 flex-shrink-0"
              />
              <div className="flex-1">
                <p className="text-sm font-medium text-error-900 dark:text-error-200">
                  Error
                </p>
                <p className="text-sm text-error-700 dark:text-error-300">
                  {error}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <ChatInput
        onSend={sendMessage}
        onCancel={cancelStream}
        disabled={isLoading}
        isStreaming={isStreaming}
      />
    </div>
  );
};
