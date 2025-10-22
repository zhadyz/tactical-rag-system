/**
 * Error Boundary Testing Component
 * FOR TESTING ONLY - DO NOT USE IN PRODUCTION
 *
 * This component intentionally throws errors to test error boundary functionality.
 * To use: Import and render in development mode only.
 */

import React, { useState } from 'react';

interface ErrorBoundaryTestProps {
  enabled?: boolean;
}

export const ErrorBoundaryTest: React.FC<ErrorBoundaryTestProps> = ({ enabled = false }) => {
  const [, setShouldThrow] = useState(false);
  const [throwInRender, setThrowInRender] = useState(false);

  if (!enabled || !import.meta.env.DEV) {
    return null;
  }

  // Intentionally throw error in render
  if (throwInRender) {
    throw new Error('Test error: Intentional error thrown in render phase');
  }

  const handleThrowError = () => {
    setShouldThrow(true);
    throw new Error('Test error: Intentional error thrown in event handler');
  };

  const handleThrowRenderError = () => {
    setThrowInRender(true);
  };

  const handleThrowAsyncError = async () => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    throw new Error('Test error: Intentional async error');
  };

  return (
    <div className="fixed bottom-24 right-4 z-50 bg-red-100 dark:bg-red-900/30 border-2 border-red-500 rounded-lg p-4 space-y-2">
      <h3 className="text-sm font-bold text-red-900 dark:text-red-200">
        Error Boundary Test (DEV ONLY)
      </h3>
      <div className="space-y-2">
        <button
          onClick={handleThrowRenderError}
          className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
        >
          Throw Render Error
        </button>
        <button
          onClick={handleThrowError}
          className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
        >
          Throw Handler Error
        </button>
        <button
          onClick={handleThrowAsyncError}
          className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
        >
          Throw Async Error
        </button>
      </div>
      <p className="text-xs text-red-800 dark:text-red-300">
        These buttons will crash the component to test error boundaries.
      </p>
    </div>
  );
};

/**
 * Component that always throws an error
 * Use for testing error boundaries
 */
export const AlwaysThrows: React.FC = () => {
  throw new Error('Test error: This component always throws');
};

/**
 * Component that throws after a delay
 * Use for testing async error handling
 */
export const ThrowsAfterDelay: React.FC<{ delay?: number }> = ({ delay = 1000 }) => {
  const [shouldThrow, setShouldThrow] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setShouldThrow(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  if (shouldThrow) {
    throw new Error(`Test error: Threw after ${delay}ms delay`);
  }

  return (
    <div className="p-4 bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-500 rounded">
      <p className="text-sm text-yellow-900 dark:text-yellow-200">
        Will throw error in {delay}ms...
      </p>
    </div>
  );
};

/**
 * Component with memory leak (for testing resource monitoring)
 */
export const MemoryLeakTest: React.FC<{ enabled?: boolean }> = ({ enabled = false }) => {
  const [leakedData, setLeakedData] = React.useState<number[]>([]);

  React.useEffect(() => {
    if (!enabled) return;

    const interval = setInterval(() => {
      // Create a large array and keep adding to state (memory leak)
      setLeakedData((prev) => [...prev, ...new Array(100000).fill(Math.random())]);
    }, 100);

    return () => clearInterval(interval);
  }, [enabled]);

  if (!enabled || !import.meta.env.DEV) {
    return null;
  }

  return (
    <div className="fixed bottom-64 right-4 z-50 bg-orange-100 dark:bg-orange-900/30 border-2 border-orange-500 rounded-lg p-4">
      <h3 className="text-sm font-bold text-orange-900 dark:text-orange-200 mb-2">
        Memory Leak Test (DEV ONLY)
      </h3>
      <p className="text-xs text-orange-800 dark:text-orange-300">
        Leaked items: {leakedData.length.toLocaleString()}
      </p>
      <p className="text-xs text-orange-800 dark:text-orange-300 mt-2">
        Watch resource monitor for memory alerts
      </p>
    </div>
  );
};
