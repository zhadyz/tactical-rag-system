import React, { useState, useRef, type KeyboardEvent } from 'react';
import { Send, Loader2, Square, Sparkles } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  onCancel?: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  onCancel,
  disabled = false,
  isStreaming = false,
  placeholder = 'Ask a question...',
}) => {
  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    const trimmedInput = input.trim();
    if (trimmedInput && !disabled && !isStreaming) {
      onSend(trimmedInput);
      setInput('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleCancel = () => {
    if (onCancel && isStreaming) {
      onCancel();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isStreaming) {
        handleSubmit();
      }
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);

    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  };

  return (
    <div className="border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 px-4 py-6">
      <div className="max-w-4xl mx-auto">
        <div className="relative">
          {/* Input container with premium styling */}
          <div className={`relative bg-neutral-50 dark:bg-neutral-900/50 rounded-2xl border-2 transition-all duration-200 ${
            isFocused
              ? 'border-primary-500 shadow-lg shadow-primary-500/10'
              : 'border-neutral-200 dark:border-neutral-800 shadow-sm'
          }`}>
            <div className="flex gap-3 items-end p-3">
              {/* Sparkles icon */}
              <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
                isFocused
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                  : 'bg-neutral-200 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400'
              }`}>
                <Sparkles size={20} strokeWidth={2} />
              </div>

              {/* Input field */}
              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleInput}
                  onKeyDown={handleKeyDown}
                  onFocus={() => setIsFocused(true)}
                  onBlur={() => setIsFocused(false)}
                  placeholder={isStreaming ? 'Generating response...' : placeholder}
                  disabled={disabled || isStreaming}
                  rows={1}
                  className="w-full px-0 py-2.5 bg-transparent text-neutral-900 dark:text-neutral-100
                           placeholder-neutral-500 dark:placeholder-neutral-400
                           focus:outline-none focus-visible:ring-0 disabled:opacity-50 disabled:cursor-not-allowed
                           resize-none overflow-hidden text-base"
                  style={{ minHeight: '40px', maxHeight: '200px' }}
                />

                {/* Character count */}
                {input.length > 0 && !isStreaming && (
                  <div className="absolute bottom-1 right-0 text-xs text-neutral-400 dark:text-neutral-500 font-medium">
                    {input.length}
                  </div>
                )}
              </div>

              {/* Send / Stop button */}
              {isStreaming ? (
                <button
                  onClick={handleCancel}
                  className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-b from-error-500 to-error-600
                           text-white shadow-sm hover:shadow-md hover:from-error-600 hover:to-error-700
                           active:scale-95 transition-all duration-150 flex items-center justify-center group"
                  aria-label="Stop generation"
                >
                  <Square size={18} fill="currentColor" className="group-hover:scale-110 transition-transform" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={disabled || !input.trim()}
                  className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-b from-primary-500 to-primary-600
                           text-white shadow-sm hover:shadow-md hover:from-primary-600 hover:to-primary-700
                           disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-sm
                           active:scale-95 transition-all duration-150 flex items-center justify-center group"
                  aria-label="Send message"
                >
                  {disabled ? (
                    <Loader2 size={18} className="animate-spin" strokeWidth={2.5} />
                  ) : (
                    <Send size={18} strokeWidth={2.5} className="group-hover:translate-x-0.5 group-hover:translate-y-[-1px] transition-transform" />
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Helper text */}
          <div className="mt-3 flex items-center justify-center gap-2 text-xs text-neutral-500 dark:text-neutral-400">
            {isStreaming ? (
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
                </span>
                <span className="font-medium">Generating response... Click stop to cancel</span>
              </div>
            ) : (
              <span className="font-medium">
                Press <kbd className="px-1.5 py-0.5 bg-neutral-200 dark:bg-neutral-800 rounded text-neutral-700 dark:text-neutral-300 font-mono text-xs">Enter</kbd> to send,
                <kbd className="ml-1 px-1.5 py-0.5 bg-neutral-200 dark:bg-neutral-800 rounded text-neutral-700 dark:text-neutral-300 font-mono text-xs">Shift + Enter</kbd> for new line
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
