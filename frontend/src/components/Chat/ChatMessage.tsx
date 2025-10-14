import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, ChevronDown, ChevronUp } from 'lucide-react';
import type { Message } from '../../types';
import { SourceCitation } from './SourceCitation';
import { PerformanceBadge } from '../Performance/PerformanceBadge';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex gap-4 p-6 animate-slide-in ${
        isUser ? 'bg-transparent' : 'bg-gray-50 dark:bg-gray-800/50'
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
        }`}
      >
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-semibold text-sm text-gray-900 dark:text-gray-100">
            {isUser ? 'You' : 'Assistant'}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
          {/* Streaming indicator */}
          {!isUser && message.isStreaming && (
            <span className="text-xs text-primary-600 dark:text-primary-400 flex items-center gap-1">
              <span className="inline-block w-1.5 h-1.5 bg-primary-600 dark:bg-primary-400 rounded-full animate-pulse"></span>
              Generating...
            </span>
          )}
        </div>

        {/* Message content with markdown */}
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {!isUser && message.content === '' && message.isStreaming ? (
            // Show loading indicator while waiting for first token
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
              <span className="text-sm">Thinking...</span>
            </div>
          ) : (
            <>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Custom styling for code blocks
                  code: ({ className, children, ...props }: any) => {
                    const inline = !className;
                    return inline ? (
                      <code
                        className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono"
                        {...props}
                      >
                        {children}
                      </code>
                    ) : (
                      <code
                        className={`${className} block p-3 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-x-auto`}
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                  // Custom styling for links
                  a: ({ children, ...props }: any) => (
                    <a
                      className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                      target="_blank"
                      rel="noopener noreferrer"
                      {...props}
                    >
                      {children}
                    </a>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
              {/* Blinking cursor when streaming */}
              {!isUser && message.isStreaming && message.content !== '' && (
                <span className="inline-block w-2 h-4 bg-primary-600 dark:bg-primary-400 animate-pulse ml-0.5"></span>
              )}
            </>
          )}
        </div>

        {/* Sources section */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
            >
              {showSources ? (
                <ChevronUp size={16} />
              ) : (
                <ChevronDown size={16} />
              )}
              <span>
                {message.sources.length} source
                {message.sources.length !== 1 ? 's' : ''}
              </span>
            </button>

            {showSources && (
              <div className="mt-3 space-y-2">
                {message.sources.map((source, index) => (
                  <SourceCitation key={index} source={source} index={index} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Performance Metrics - Simple display without store */}
        {!isUser && message.metadata && 'processing_time_ms' in message.metadata && message.metadata.processing_time_ms && (
          <PerformanceBadge metadata={message.metadata as any} />
        )}
      </div>
    </div>
  );
};
