import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';

export type ConnectionStatus = 'online' | 'offline' | 'reconnecting';

export interface ConnectionState {
  status: ConnectionStatus;
  isOnline: boolean;
  lastChecked: Date | null;
  error: string | null;
}

const HEALTH_CHECK_INTERVAL = 30000; // 30 seconds
const RECONNECT_CHECK_INTERVAL = 5000; // 5 seconds when offline

export const useConnectionStatus = () => {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: 'online',
    isOnline: true,
    lastChecked: null,
    error: null,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isCheckingRef = useRef(false);

  const checkBackendHealth = useCallback(async () => {
    // Prevent concurrent health checks
    if (isCheckingRef.current) return;

    isCheckingRef.current = true;

    try {
      await api.health();

      setConnectionState({
        status: 'online',
        isOnline: true,
        lastChecked: new Date(),
        error: null,
      });
    } catch (err: any) {
      console.error('Backend health check failed:', err);

      setConnectionState({
        status: 'offline',
        isOnline: false,
        lastChecked: new Date(),
        error: err.message || 'Backend unavailable',
      });
    } finally {
      isCheckingRef.current = false;
    }
  }, []);

  // Handle browser online/offline events
  useEffect(() => {
    const handleOnline = () => {
      console.log('Browser detected online');
      setConnectionState(prev => ({
        ...prev,
        status: 'reconnecting',
      }));
      // Immediately check backend health when browser comes online
      checkBackendHealth();
    };

    const handleOffline = () => {
      console.log('Browser detected offline');
      setConnectionState({
        status: 'offline',
        isOnline: false,
        lastChecked: new Date(),
        error: 'No internet connection',
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [checkBackendHealth]);

  // Periodic health checks
  useEffect(() => {
    // Initial check on mount
    checkBackendHealth();

    // Set up interval based on current status
    const interval = connectionState.status === 'offline'
      ? RECONNECT_CHECK_INTERVAL
      : HEALTH_CHECK_INTERVAL;

    intervalRef.current = setInterval(() => {
      checkBackendHealth();
    }, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [checkBackendHealth, connectionState.status]);

  // Force a health check
  const forceCheck = useCallback(() => {
    checkBackendHealth();
  }, [checkBackendHealth]);

  return {
    ...connectionState,
    forceCheck,
  };
};
