import { useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

interface UseWebSocketOptions {
  url?: string;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
  onMessage?: (data: any) => void;
}

export const useWebSocket = ({
  url = 'http://localhost:8000',
  onConnect,
  onDisconnect,
  onError,
  onMessage,
}: UseWebSocketOptions = {}) => {
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Initialize socket connection
    socketRef.current = io(url, {
      transports: ['websocket'],
      autoConnect: false,
    });

    const socket = socketRef.current;

    // Set up event listeners
    socket.on('connect', () => {
      console.log('WebSocket connected');
      onConnect?.();
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      onDisconnect?.();
    });

    socket.on('error', (error: Error) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    });

    socket.on('message', (data: any) => {
      onMessage?.(data);
    });

    // Connect to socket
    socket.connect();

    // Cleanup on unmount
    return () => {
      socket.disconnect();
    };
  }, [url, onConnect, onDisconnect, onError, onMessage]);

  const sendMessage = useCallback((event: string, data: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);

  const disconnect = useCallback(() => {
    socketRef.current?.disconnect();
  }, []);

  const reconnect = useCallback(() => {
    socketRef.current?.connect();
  }, []);

  return {
    socket: socketRef.current,
    sendMessage,
    disconnect,
    reconnect,
    isConnected: socketRef.current?.connected ?? false,
  };
};
