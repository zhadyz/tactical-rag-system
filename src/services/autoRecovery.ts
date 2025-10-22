/**
 * Auto-Recovery Service
 * Handles automatic recovery from common failures in field deployment
 */

import * as React from 'react';
import { api } from './api';

export interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'down';
  latency: number;
  lastCheck: Date;
  consecutiveFailures: number;
  error?: string;
}

export interface RecoveryAction {
  type: 'reconnect' | 'reload' | 'clear-cache' | 'notify';
  timestamp: Date;
  reason: string;
  success: boolean;
}

export interface AutoRecoveryConfig {
  healthCheckInterval: number; // ms
  maxConsecutiveFailures: number;
  reconnectDelay: number; // ms
  maxReconnectAttempts: number;
  enableAutoReload: boolean;
}

const DEFAULT_CONFIG: AutoRecoveryConfig = {
  healthCheckInterval: 10000, // 10 seconds
  maxConsecutiveFailures: 3,
  reconnectDelay: 2000, // 2 seconds
  maxReconnectAttempts: 5,
  enableAutoReload: false, // Disabled by default for safety
};

type HealthCheckCallback = (result: HealthCheckResult) => void;
type RecoveryCallback = (action: RecoveryAction) => void;

class AutoRecoveryService {
  private config: AutoRecoveryConfig;
  private healthCheckInterval: number | null = null;
  private healthStatus: HealthCheckResult = {
    status: 'healthy',
    latency: 0,
    lastCheck: new Date(),
    consecutiveFailures: 0,
  };
  private recoveryHistory: RecoveryAction[] = [];
  private isMonitoring: boolean = false;
  private reconnectAttempts: number = 0;
  private onHealthCheck?: HealthCheckCallback;
  private onRecovery?: RecoveryCallback;

  constructor(config: Partial<AutoRecoveryConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Start health monitoring
   */
  startMonitoring(
    onHealthCheck?: HealthCheckCallback,
    onRecovery?: RecoveryCallback
  ) {
    if (this.isMonitoring) {
      return;
    }

    this.isMonitoring = true;
    this.onHealthCheck = onHealthCheck;
    this.onRecovery = onRecovery;

    // Initial health check
    this.performHealthCheck();

    // Start periodic health checks
    this.healthCheckInterval = window.setInterval(() => {
      this.performHealthCheck();
    }, this.config.healthCheckInterval);
  }

  /**
   * Stop health monitoring
   */
  stopMonitoring() {
    this.isMonitoring = false;

    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
  }

  /**
   * Perform a health check
   */
  private async performHealthCheck() {
    const startTime = performance.now();

    try {
      const response = await api.health();
      const latency = performance.now() - startTime;

      const result: HealthCheckResult = {
        status: response.status === 'healthy' ? 'healthy' : 'degraded',
        latency,
        lastCheck: new Date(),
        consecutiveFailures: 0,
      };

      // Reset failure counter on success
      this.reconnectAttempts = 0;

      this.healthStatus = result;
      this.onHealthCheck?.(result);
    } catch (error: any) {
      const latency = performance.now() - startTime;

      this.healthStatus = {
        status: 'down',
        latency,
        lastCheck: new Date(),
        consecutiveFailures: this.healthStatus.consecutiveFailures + 1,
        error: error.message,
      };

      this.onHealthCheck?.(this.healthStatus);

      // Trigger recovery if threshold exceeded
      if (
        this.healthStatus.consecutiveFailures >= this.config.maxConsecutiveFailures
      ) {
        await this.attemptRecovery();
      }
    }
  }

  /**
   * Attempt automatic recovery
   */
  private async attemptRecovery() {
    // Don't attempt recovery if already at max attempts
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.logRecoveryAction({
        type: 'notify',
        timestamp: new Date(),
        reason: 'Max reconnect attempts reached',
        success: false,
      });
      return;
    }

    this.reconnectAttempts++;

    // Try reconnection
    await this.attemptReconnect();

    // If reconnection fails multiple times, try cache clear
    if (this.reconnectAttempts >= 2) {
      await this.attemptCacheClear();
    }

    // If still failing and auto-reload is enabled, reload the page
    if (
      this.reconnectAttempts >= this.config.maxReconnectAttempts &&
      this.config.enableAutoReload
    ) {
      await this.attemptReload();
    }
  }

  /**
   * Attempt to reconnect to backend
   */
  private async attemptReconnect() {
    await new Promise((resolve) => setTimeout(resolve, this.config.reconnectDelay));

    try {
      await api.health();

      this.logRecoveryAction({
        type: 'reconnect',
        timestamp: new Date(),
        reason: `Reconnected after ${this.reconnectAttempts} attempts`,
        success: true,
      });

      // Reset failure count on successful reconnect
      this.healthStatus.consecutiveFailures = 0;
      this.reconnectAttempts = 0;
    } catch (error: any) {
      this.logRecoveryAction({
        type: 'reconnect',
        timestamp: new Date(),
        reason: `Reconnect attempt ${this.reconnectAttempts} failed: ${error.message}`,
        success: false,
      });
    }
  }

  /**
   * Attempt to clear cache and memory
   */
  private async attemptCacheClear() {
    try {
      // Clear browser cache if supported
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map((name) => caches.delete(name)));
      }

      // Clear local storage (except error logs)
      const errorLogs = localStorage.getItem('error-logs');
      localStorage.clear();
      if (errorLogs) {
        localStorage.setItem('error-logs', errorLogs);
      }

      // Try to clear backend cache
      try {
        await api.clearCacheAndMemory();
      } catch {
        // Backend might be down, silently fail
      }

      this.logRecoveryAction({
        type: 'clear-cache',
        timestamp: new Date(),
        reason: 'Cleared cache after connection failures',
        success: true,
      });
    } catch (error: any) {
      this.logRecoveryAction({
        type: 'clear-cache',
        timestamp: new Date(),
        reason: `Cache clear failed: ${error.message}`,
        success: false,
      });
    }
  }

  /**
   * Reload the page (last resort)
   */
  private async attemptReload() {
    this.logRecoveryAction({
      type: 'reload',
      timestamp: new Date(),
      reason: 'Auto-reload triggered after max reconnect attempts',
      success: true,
    });

    // Save recovery history before reload
    localStorage.setItem(
      'recovery-history',
      JSON.stringify(this.recoveryHistory)
    );

    // Reload after a short delay
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  }

  /**
   * Log a recovery action
   */
  private logRecoveryAction(action: RecoveryAction) {
    this.recoveryHistory.push(action);

    // Keep only last 50 actions
    if (this.recoveryHistory.length > 50) {
      this.recoveryHistory = this.recoveryHistory.slice(-50);
    }

    // Persist to localStorage
    localStorage.setItem(
      'recovery-history',
      JSON.stringify(this.recoveryHistory)
    );

    // Notify callback
    this.onRecovery?.(action);
  }

  /**
   * Get current health status
   */
  getHealthStatus(): HealthCheckResult {
    return this.healthStatus;
  }

  /**
   * Get recovery history
   */
  getRecoveryHistory(): RecoveryAction[] {
    return this.recoveryHistory;
  }

  /**
   * Load recovery history from localStorage
   */
  loadRecoveryHistory() {
    try {
      const stored = localStorage.getItem('recovery-history');
      if (stored) {
        this.recoveryHistory = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load recovery history:', error);
    }
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<AutoRecoveryConfig>) {
    this.config = { ...this.config, ...config };

    // Restart monitoring with new config if currently monitoring
    if (this.isMonitoring) {
      this.stopMonitoring();
      this.startMonitoring(this.onHealthCheck, this.onRecovery);
    }
  }

  /**
   * Get current configuration
   */
  getConfig(): AutoRecoveryConfig {
    return this.config;
  }

  /**
   * Manual health check
   */
  async checkHealth(): Promise<HealthCheckResult> {
    await this.performHealthCheck();
    return this.healthStatus;
  }

  /**
   * Manual recovery trigger
   */
  async triggerRecovery() {
    await this.attemptRecovery();
  }
}

// Singleton instance
export const autoRecoveryService = new AutoRecoveryService();

// Load recovery history on initialization
autoRecoveryService.loadRecoveryHistory();

/**
 * React hook for auto-recovery
 */
export function useAutoRecovery(
  enabled: boolean = true,
  config?: Partial<AutoRecoveryConfig>
) {
  const [healthStatus, setHealthStatus] = React.useState<HealthCheckResult>(
    autoRecoveryService.getHealthStatus()
  );
  const [recoveryActions, setRecoveryActions] = React.useState<RecoveryAction[]>(
    autoRecoveryService.getRecoveryHistory()
  );

  React.useEffect(() => {
    if (config) {
      autoRecoveryService.updateConfig(config);
    }
  }, [config]);

  React.useEffect(() => {
    if (!enabled) {
      autoRecoveryService.stopMonitoring();
      return;
    }

    const handleHealthCheck = (result: HealthCheckResult) => {
      setHealthStatus(result);
    };

    const handleRecovery = (action: RecoveryAction) => {
      setRecoveryActions((prev) => [...prev, action]);
    };

    autoRecoveryService.startMonitoring(handleHealthCheck, handleRecovery);

    return () => {
      autoRecoveryService.stopMonitoring();
    };
  }, [enabled]);

  const triggerRecovery = React.useCallback(async () => {
    await autoRecoveryService.triggerRecovery();
  }, []);

  const checkHealth = React.useCallback(async () => {
    return await autoRecoveryService.checkHealth();
  }, []);

  return {
    healthStatus,
    recoveryActions,
    triggerRecovery,
    checkHealth,
  };
}
