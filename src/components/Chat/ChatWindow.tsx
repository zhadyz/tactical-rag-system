import React, { useEffect, useRef } from 'react';
import { AlertCircle, MessageSquare, Sparkles, BookOpen, FileSearch } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { ErrorBoundary } from '../ErrorBoundary/ErrorBoundary';
import useStore from '../../store/useStore';
import { useChat } from '../../hooks/useChat';

export const ChatWindow: React.FC = () => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messages = useStore((state) => state.messages);
  const isLoading = useStore((state) => state.isLoading);
  const isStreaming = useStore((state) => state.isStreaming);
  const error = useStore((state) => state.error);

  const { sendMessage, cancelStream, isOnline } = useChat();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-neutral-50 dark:bg-neutral-950">
      {/* Messages container */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          // Empty state - Enterprise-grade design
          <div className="h-full flex items-center justify-center px-4 py-12">
            <div className="text-center max-w-2xl mx-auto space-y-8 animate-fade-in">
              {/* Hero icon */}
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 dark:to-primary-800/20 rounded-3xl shadow-lg">
                <MessageSquare
                  className="w-10 h-10 text-primary-600 dark:text-primary-400"
                  strokeWidth={2}
                />
              </div>

              {/* Heading */}
              <div className="space-y-3">
                <h1 className="text-4xl font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                  Welcome to Tactical RAG
                </h1>
                <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto leading-relaxed">
                  Ask questions about your documents and get intelligent, context-aware answers
                  powered by advanced retrieval and reasoning.
                </p>
              </div>

              {/* Suggestion cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
                <div className="group p-5 bg-neutral-50 dark:bg-neutral-900/50 rounded-2xl border border-neutral-200 dark:border-neutral-800 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-lg transition-all duration-200 cursor-pointer">
                  <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
                    <Sparkles size={20} className="text-primary-600 dark:text-primary-400" strokeWidth={2} />
                  </div>
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                    Explore Topics
                  </h3>
                  <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
                    What are the main topics discussed in the documents?
                  </p>
                </div>

                <div className="group p-5 bg-neutral-50 dark:bg-neutral-900/50 rounded-2xl border border-neutral-200 dark:border-neutral-800 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-lg transition-all duration-200 cursor-pointer">
                  <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
                    <BookOpen size={20} className="text-primary-600 dark:text-primary-400" strokeWidth={2} />
                  </div>
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                    Summarize Content
                  </h3>
                  <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
                    Summarize the key findings and important insights
                  </p>
                </div>

                <div className="group p-5 bg-neutral-50 dark:bg-neutral-900/50 rounded-2xl border border-neutral-200 dark:border-neutral-800 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-lg transition-all duration-200 cursor-pointer">
                  <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
                    <FileSearch size={20} className="text-primary-600 dark:text-primary-400" strokeWidth={2} />
                  </div>
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                    Compare Sections
                  </h3>
                  <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
                    Compare and contrast different sections or documents
                  </p>
                </div>
              </div>

              {/* Subtle footer hint */}
              <p className="text-xs text-neutral-500 dark:text-neutral-500 font-medium pt-4">
                Start by typing your question below
              </p>
            </div>
          </div>
        ) : (
          // Messages list
          <div className="max-w-4xl mx-auto w-full">
            {messages.map((message) => (
              <ErrorBoundary key={message.id} componentName="ChatMessage">
                <ChatMessage message={message} />
              </ErrorBoundary>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Error message - Enterprise styling with helpful suggestions */}
        {error && (
          <div className="max-w-4xl mx-auto w-full px-6 pb-4">
            <div className="flex items-start gap-3 p-4 bg-error-50 dark:bg-error-900/30 border border-error-200 dark:border-error-800 rounded-xl shadow-sm animate-slide-in">
              <div className="flex-shrink-0 w-8 h-8 bg-error-100 dark:bg-error-900/50 rounded-lg flex items-center justify-center">
                <AlertCircle
                  size={18}
                  className="text-error-600 dark:text-error-400"
                  strokeWidth={2}
                />
              </div>
              <div className="flex-1 pt-0.5">
                <p className="text-sm font-semibold text-error-900 dark:text-error-200 mb-0.5">
                  Unable to Process Query
                </p>
                <p className="text-sm text-error-700 dark:text-error-300 leading-relaxed mb-2">
                  {error}
                </p>
                <div className="text-xs text-error-600 dark:text-error-400 space-y-1">
                  <p className="font-medium">Suggestions:</p>
                  <ul className="list-disc list-inside space-y-0.5 ml-1">
                    <li>Check if the backend service is running</li>
                    <li>Verify documents are uploaded and indexed</li>
                    <li>Try rephrasing your question</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <ErrorBoundary componentName="ChatInput">
        <ChatInput
          onSend={sendMessage}
          onCancel={cancelStream}
          disabled={isLoading || !isOnline}
          isStreaming={isStreaming}
          isOffline={!isOnline}
        />
      </ErrorBoundary>
    </div>
  );
};
