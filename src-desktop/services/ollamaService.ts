/**
 * Ollama Service
 * Manages Qwen model detection and configuration
 */

import { invoke } from '@tauri-apps/api/core';

export interface OllamaStatus {
  installed: boolean;
  running: boolean;
  version?: string;
  models: string[];
  qwen_available: boolean;
  recommended_model: string;
}

/**
 * Get current Ollama installation status
 */
export async function getOllamaStatus(): Promise<OllamaStatus> {
  try {
    const status = await invoke<OllamaStatus>('get_ollama_status');
    return status;
  } catch (error) {
    console.error('Failed to get Ollama status:', error);
    throw error;
  }
}

/**
 * Pull a specific Qwen model
 */
export async function pullQwenModel(modelName: string): Promise<void> {
  try {
    await invoke('pull_qwen_model', { model: modelName });
    console.log(`Successfully pulled model: ${modelName}`);
  } catch (error) {
    console.error('Failed to pull Qwen model:', error);
    throw error;
  }
}

/**
 * Verify Qwen model is installed, pull if not
 */
export async function verifyQwen(): Promise<void> {
  try {
    await invoke('verify_qwen');
    console.log('Qwen model verified and ready');
  } catch (error) {
    console.error('Failed to verify Qwen:', error);
    throw error;
  }
}

/**
 * Get recommended Qwen model name
 */
export async function getRecommendedQwenModel(): Promise<string> {
  try {
    const model = await invoke<string>('get_recommended_qwen_model');
    return model;
  } catch (error) {
    console.error('Failed to get recommended model:', error);
    throw error;
  }
}

/**
 * Monitor Ollama status with polling
 */
export function monitorOllamaStatus(
  onStatusChange: (status: OllamaStatus) => void,
  interval: number = 10000
): () => void {
  const timer = setInterval(async () => {
    try {
      const status = await getOllamaStatus();
      onStatusChange(status);
    } catch (error) {
      console.error('Ollama monitoring error:', error);
    }
  }, interval);

  // Return cleanup function
  return () => clearInterval(timer);
}
