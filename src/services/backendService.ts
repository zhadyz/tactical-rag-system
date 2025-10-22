/**
 * Backend Sidecar Service
 * Interacts with Tauri backend sidecar commands
 */

import { invoke } from '@tauri-apps/api/core';

export interface BackendStatus {
  running: boolean;
  healthy: boolean;
  port: number;
  last_check: string;
  error?: string;
}

/**
 * Start the backend sidecar process
 */
export async function startBackend(): Promise<void> {
  try {
    await invoke('start_backend');
    console.log('Backend started successfully');
  } catch (error) {
    console.error('Failed to start backend:', error);
    throw error;
  }
}

/**
 * Stop the backend sidecar process
 */
export async function stopBackend(): Promise<void> {
  try {
    await invoke('stop_backend');
    console.log('Backend stopped successfully');
  } catch (error) {
    console.error('Failed to stop backend:', error);
    throw error;
  }
}

/**
 * Get current backend status
 */
export async function getBackendStatus(): Promise<BackendStatus> {
  try {
    const status = await invoke<BackendStatus>('get_backend_status');
    return status;
  } catch (error) {
    console.error('Failed to get backend status:', error);
    throw error;
  }
}

/**
 * Monitor backend health with polling
 */
export function monitorBackendHealth(
  onStatusChange: (status: BackendStatus) => void,
  interval: number = 5000
): () => void {
  const timer = setInterval(async () => {
    try {
      const status = await getBackendStatus();
      onStatusChange(status);
    } catch (error) {
      console.error('Health monitoring error:', error);
    }
  }, interval);

  // Return cleanup function
  return () => clearInterval(timer);
}
