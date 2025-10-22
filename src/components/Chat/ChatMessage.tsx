import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, ChevronDown, ChevronUp, Clock } from 'lucide-react';
import type { Message } from '../../types';
import { SourceCitation } from './SourceCitation';

interface ChatMessageProps {
  message: Message;
}

// PERFORMANCE OPTIMIZATION: Custom comparison function for React.memo
// This prevents unnecessary re-renders when message content hasn't actually changed
const arePropsEqual = (prevProps: ChatMessageProps, nextProps: ChatMessageProps): boolean => {
  const prevMsg = prevProps.message;
  const nextMsg = nextProps.message;

  // If IDs differ, messages are different
  if (prevMsg.id !== nextMsg.id) return false;

  // If content changed, re-render (critical for streaming updates)
  if (prevMsg.content !== nextMsg.content) return false;

  // If streaming status changed, re-render
  if (prevMsg.isStreaming !== nextMsg.isStreaming) return false;

  // If sources changed (length or reference), re-render
  if (prevMsg.sources?.length !== nextMsg.sources?.length) return false;

  // If metadata changed (shallow comparison for processing time)
  if (prevMsg.metadata?.processing_time_ms !== nextMsg.metadata?.processing_time_ms) return false;

  // Props are equal - skip re-render for performance
  return true;
};

export const ChatMessage = React.memo<ChatMessageProps>(({ message }) => {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  return (
    <div
      className={`group flex gap-5 px-6 py-8 animate-slide-in transition-colors duration-200 ${
        isUser
          ? 'bg-transparent hover:bg-neutral-50/50 dark:hover:bg-neutral-900/30'
          : 'bg-neutral-50/70 dark:bg-neutral-900/40 hover:bg-neutral-100/70 dark:hover:bg-neutral-900/60'
      }`}
      role="article"
      aria-label={`${isUser ? 'Your' : 'Assistant'} message from ${new Date(message.timestamp).toLocaleTimeString()}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-10 h-10 rounded-2xl flex items-center justify-center shadow-sm transition-all duration-200 ${
          isUser
            ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white group-hover:shadow-md group-hover:from-primary-600 group-hover:to-primary-700'
            : 'bg-gradient-to-br from-neutral-200 to-neutral-300 dark:from-neutral-700 dark:to-neutral-800 text-neutral-700 dark:text-neutral-200 group-hover:shadow-md'
        }`}
        aria-hidden="true"
      >
        {isUser ? <User size={20} strokeWidth={2} /> : <Bot size={20} strokeWidth={2} />}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-3">
        {/* Header */}
        <div className="flex items-center gap-3 flex-wrap">
          <span className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
            {isUser ? 'You' : 'Assistant'}
          </span>
          <span className="text-xs text-neutral-500 dark:text-neutral-400 font-medium">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
          {/* Streaming indicator */}
          {!isUser && message.isStreaming && (
            <span className="inline-flex items-center gap-1.5 px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 rounded-lg text-xs font-medium" role="status" aria-live="polite">
              <span className="relative flex h-2 w-2" aria-hidden="true">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
              </span>
              Generating
            </span>
          )}
          {/* Processing time badge - subtle and elegant */}
          {!isUser && !message.isStreaming && message.metadata && 'processing_time_ms' in message.metadata && message.metadata.processing_time_ms && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 rounded-lg text-xs font-medium">
              <Clock size={12} strokeWidth={2} />
              {(message.metadata.processing_time_ms / 1000).toFixed(2)}s
            </span>
          )}
        </div>

        {/* Message content with markdown */}
        <div className="prose prose-sm dark:prose-invert max-w-none prose-neutral
                        prose-headings:font-semibold prose-headings:text-neutral-900 dark:prose-headings:text-neutral-100
                        prose-p:text-neutral-700 dark:prose-p:text-neutral-300 prose-p:leading-relaxed
                        prose-a:text-primary-600 dark:prose-a:text-primary-400 prose-a:no-underline hover:prose-a:underline
                        prose-code:text-primary-700 dark:prose-code:text-primary-300 prose-code:bg-neutral-100 dark:prose-code:bg-neutral-800
                        prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:font-medium prose-code:before:content-none prose-code:after:content-none
                        prose-pre:bg-neutral-900 dark:prose-pre:bg-neutral-950 prose-pre:shadow-lg prose-pre:border prose-pre:border-neutral-200 dark:prose-pre:border-neutral-800
                        prose-strong:text-neutral-900 dark:prose-strong:text-neutral-100 prose-strong:font-semibold
                        prose-ul:text-neutral-700 dark:prose-ul:text-neutral-300
                        prose-ol:text-neutral-700 dark:prose-ol:text-neutral-300">
          {!isUser && message.content === '' && message.isStreaming ? (
            // Show loading indicator while waiting for first token
            <div className="flex items-center gap-3 text-neutral-500 dark:text-neutral-400" role="status" aria-live="polite" aria-label="Assistant is thinking">
              <div className="flex gap-1.5" aria-hidden="true">
                <span className="w-2 h-2 bg-neutral-400 dark:bg-neutral-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-neutral-400 dark:bg-neutral-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-neutral-400 dark:bg-neutral-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
              <span className="text-sm font-medium">Thinking...</span>
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
                      <code {...props}>
                        {children}
                      </code>
                    ) : (
                      <code
                        className={`${className} block p-4 bg-neutral-900 dark:bg-neutral-950 rounded-xl overflow-x-auto text-sm`}
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                  // Custom styling for links
                  a: ({ children, ...props }: any) => (
                    <a
                      className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 font-medium transition-colors"
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
                <span className="inline-block w-0.5 h-5 bg-primary-500 dark:bg-primary-400 animate-pulse ml-0.5 rounded-sm"></span>
              )}
            </>
          )}
        </div>

        {/* Sources section */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-5 space-y-3">
            <button
              onClick={() => setShowSources(!showSources)}
              className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300
                         hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800
                         rounded-xl transition-all duration-150 group/sources"
              aria-expanded={showSources}
              aria-label={`${showSources ? 'Hide' : 'Show'} ${message.sources.length} cited source${message.sources.length !== 1 ? 's' : ''}`}
            >
              {showSources ? (
                <ChevronUp size={16} className="transition-transform group-hover/sources:translate-y-[-1px]" aria-hidden="true" />
              ) : (
                <ChevronDown size={16} className="transition-transform group-hover/sources:translate-y-[1px]" aria-hidden="true" />
              )}
              <span>
                {message.sources.length} source{message.sources.length !== 1 ? 's' : ''} cited
              </span>
            </button>

            {showSources && (
              <div className="space-y-2 animate-slide-up" role="region" aria-label="Source citations">
                {message.sources.filter(s => s && s.metadata).map((source, index) => (
                  <SourceCitation key={source.metadata.source + index} source={source} index={index} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}, arePropsEqual);
