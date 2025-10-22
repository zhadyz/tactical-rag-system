import { useRef, useCallback, useEffect } from 'react';

/**
 * PERFORMANCE OPTIMIZATION: Throttle callback execution using requestAnimationFrame
 * This ensures UI updates happen at most once per frame (60fps max)
 *
 * @param callback - Function to throttle
 * @param delay - Minimum delay between calls in ms (default: 16ms ~= 60fps)
 * @returns Throttled callback function
 */
export function useThrottledCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 16
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastRunRef = useRef<number>(0);
  const pendingArgsRef = useRef<Parameters<T> | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return useCallback(
    (...args: Parameters<T>) => {
      // Store the latest arguments
      pendingArgsRef.current = args;

      const now = Date.now();
      const timeSinceLastRun = now - lastRunRef.current;

      // If enough time has passed, execute immediately
      if (timeSinceLastRun >= delay) {
        lastRunRef.current = now;
        pendingArgsRef.current = null;
        callback(...args);
      } else if (!timeoutRef.current) {
        // Schedule execution for later
        const remainingTime = delay - timeSinceLastRun;
        timeoutRef.current = setTimeout(() => {
          timeoutRef.current = null;
          lastRunRef.current = Date.now();
          if (pendingArgsRef.current) {
            callback(...pendingArgsRef.current);
            pendingArgsRef.current = null;
          }
        }, remainingTime);
      }
      // If a timeout is already scheduled, it will use the latest args
    },
    [callback, delay]
  );
}

/**
 * PERFORMANCE OPTIMIZATION: Debounced callback that accumulates arguments
 * Useful for batching token updates during streaming
 *
 * @param callback - Function to debounce
 * @param delay - Delay in ms
 * @returns Debounced callback function
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    },
    [callback, delay]
  );
}
