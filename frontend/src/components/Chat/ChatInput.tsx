import React, { useState, useRef, type KeyboardEvent } from 'react';
import { Send, Loader2, Square } from 'lucide-react';

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
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex gap-3 items-end">
          {/* Input field */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder={isStreaming ? 'Generating response...' : placeholder}
              disabled={disabled || isStreaming}
              rows={1}
              className="w-full px-4 py-3 pr-12 rounded-lg border border-gray-300 dark:border-gray-600
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                       placeholder-gray-500 dark:placeholder-gray-400
                       focus:ring-2 focus:ring-primary-500 focus:border-transparent
                       disabled:opacity-50 disabled:cursor-not-allowed
                       resize-none overflow-hidden"
              style={{ minHeight: '48px', maxHeight: '200px' }}
            />

            {/* Character count (optional) */}
            {input.length > 0 && (
              <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                {input.length}
              </div>
            )}
          </div>

          {/* Send / Stop button */}
          {isStreaming ? (
            <button
              onClick={handleCancel}
              className="flex-shrink-0 w-12 h-12 rounded-lg bg-error-600 text-white
                       hover:bg-error-700 transition-colors flex items-center justify-center"
              aria-label="Stop generation"
            >
              <Square size={20} fill="currentColor" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={disabled || !input.trim()}
              className="flex-shrink-0 w-12 h-12 rounded-lg bg-primary-600 text-white
                       hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors flex items-center justify-center"
              aria-label="Send message"
            >
              {disabled ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <Send size={20} />
              )}
            </button>
          )}
        </div>

        {/* Helper text */}
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
          {isStreaming
            ? 'Generating response... Click the stop button to cancel'
            : 'Press Enter to send, Shift + Enter for new line'}
        </div>
      </div>
    </div>
  );
};
