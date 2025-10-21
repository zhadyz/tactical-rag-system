/**
 * Resource Monitoring Utilities
 * Tracks memory, disk, and performance for field deployment
 */

export interface ResourceMetrics {
  memory: {
    used: number;
    total: number;
    percentage: number;
    jsHeapSize?: number;
    jsHeapSizeLimit?: number;
  };
  performance: {
    fps: number;
    lastFrameTime: number;
  };
  storage: {
    used: number;
    quota: number;
    percentage: number;
  } | null;
}

export interface ResourceThresholds {
  memoryWarning: number; // Percentage
  memoryError: number; // Percentage
  storageWarning: number; // Percentage
  storageError: number; // Percentage
  fpsWarning: number; // FPS threshold
}

export const DEFAULT_THRESHOLDS: ResourceThresholds = {
  memoryWarning: 70,
  memoryError: 90,
  storageWarning: 80,
  storageError: 95,
  fpsWarning: 30,
};

export type ResourceAlert = {
  level: 'warning' | 'error';
  type: 'memory' | 'storage' | 'performance';
  message: string;
  value: number;
  threshold: number;
};

class ResourceMonitor {
  private thresholds: ResourceThresholds;
  private alerts: ResourceAlert[] = [];
  private lastFrameTime: number = performance.now();
  private frameCount: number = 0;
  private fps: number = 60;
  private isMonitoring: boolean = false;
  private monitoringInterval: number | null = null;
  private onAlertCallback?: (alert: ResourceAlert) => void;

  constructor(thresholds: ResourceThresholds = DEFAULT_THRESHOLDS) {
    this.thresholds = thresholds;
  }

  /**
   * Get current memory usage
   */
  getMemoryMetrics() {
    const memory = (performance as any).memory;

    if (memory) {
      const used = memory.usedJSHeapSize;
      const total = memory.jsHeapSizeLimit;
      const percentage = (used / total) * 100;

      return {
        used,
        total,
        percentage,
        jsHeapSize: memory.jsHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit,
      };
    }

    // Fallback for browsers without memory API
    return {
      used: 0,
      total: 0,
      percentage: 0,
    };
  }

  /**
   * Get storage quota metrics
   */
  async getStorageMetrics() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate();
        const used = estimate.usage || 0;
        const quota = estimate.quota || 0;
        const percentage = quota > 0 ? (used / quota) * 100 : 0;

        return {
          used,
          quota,
          percentage,
        };
      } catch (err) {
        console.error('Failed to get storage estimate:', err);
        return null;
      }
    }

    return null;
  }

  /**
   * Update FPS calculation
   */
  private updateFPS() {
    const now = performance.now();
    const delta = now - this.lastFrameTime;
    this.lastFrameTime = now;
    this.frameCount++;

    // Update FPS every 60 frames
    if (this.frameCount >= 60) {
      this.fps = Math.round(1000 / (delta / 60));
      this.frameCount = 0;
    }

    if (this.isMonitoring) {
      requestAnimationFrame(() => this.updateFPS());
    }
  }

  /**
   * Get performance metrics
   */
  getPerformanceMetrics() {
    return {
      fps: this.fps,
      lastFrameTime: this.lastFrameTime,
    };
  }

  /**
   * Get all resource metrics
   */
  async getMetrics(): Promise<ResourceMetrics> {
    const memory = this.getMemoryMetrics();
    const performance = this.getPerformanceMetrics();
    const storage = await this.getStorageMetrics();

    return {
      memory,
      performance,
      storage,
    };
  }

  /**
   * Check if any thresholds are exceeded
   */
  async checkThresholds(): Promise<ResourceAlert[]> {
    const metrics = await this.getMetrics();
    const newAlerts: ResourceAlert[] = [];

    // Check memory
    if (metrics.memory.percentage >= this.thresholds.memoryError) {
      newAlerts.push({
        level: 'error',
        type: 'memory',
        message: `Critical memory usage: ${metrics.memory.percentage.toFixed(1)}%`,
        value: metrics.memory.percentage,
        threshold: this.thresholds.memoryError,
      });
    } else if (metrics.memory.percentage >= this.thresholds.memoryWarning) {
      newAlerts.push({
        level: 'warning',
        type: 'memory',
        message: `High memory usage: ${metrics.memory.percentage.toFixed(1)}%`,
        value: metrics.memory.percentage,
        threshold: this.thresholds.memoryWarning,
      });
    }

    // Check storage
    if (metrics.storage) {
      if (metrics.storage.percentage >= this.thresholds.storageError) {
        newAlerts.push({
          level: 'error',
          type: 'storage',
          message: `Critical disk usage: ${metrics.storage.percentage.toFixed(1)}%`,
          value: metrics.storage.percentage,
          threshold: this.thresholds.storageError,
        });
      } else if (metrics.storage.percentage >= this.thresholds.storageWarning) {
        newAlerts.push({
          level: 'warning',
          type: 'storage',
          message: `High disk usage: ${metrics.storage.percentage.toFixed(1)}%`,
          value: metrics.storage.percentage,
          threshold: this.thresholds.storageWarning,
        });
      }
    }

    // Check FPS
    if (metrics.performance.fps < this.thresholds.fpsWarning && metrics.performance.fps > 0) {
      newAlerts.push({
        level: 'warning',
        type: 'performance',
        message: `Low FPS detected: ${metrics.performance.fps}`,
        value: metrics.performance.fps,
        threshold: this.thresholds.fpsWarning,
      });
    }

    // Store alerts
    this.alerts = newAlerts;

    // Trigger callback for each new alert
    if (this.onAlertCallback) {
      newAlerts.forEach((alert) => this.onAlertCallback?.(alert));
    }

    return newAlerts;
  }

  /**
   * Start continuous monitoring
   */
  startMonitoring(intervalMs: number = 5000, onAlert?: (alert: ResourceAlert) => void) {
    if (this.isMonitoring) {
      return;
    }

    this.isMonitoring = true;
    this.onAlertCallback = onAlert;

    // Start FPS tracking
    requestAnimationFrame(() => this.updateFPS());

    // Start periodic threshold checks
    this.monitoringInterval = window.setInterval(() => {
      this.checkThresholds();
    }, intervalMs);
  }

  /**
   * Stop monitoring
   */
  stopMonitoring() {
    this.isMonitoring = false;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  /**
   * Get current alerts
   */
  getAlerts(): ResourceAlert[] {
    return this.alerts;
  }

  /**
   * Clear all alerts
   */
  clearAlerts() {
    this.alerts = [];
  }

  /**
   * Format bytes to human-readable string
   */
  static formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Get system health status
   */
  async getHealthStatus(): Promise<'healthy' | 'warning' | 'critical'> {
    const alerts = await this.checkThresholds();

    if (alerts.some((a) => a.level === 'error')) {
      return 'critical';
    } else if (alerts.some((a) => a.level === 'warning')) {
      return 'warning';
    }

    return 'healthy';
  }
}

// Singleton instance
export const resourceMonitor = new ResourceMonitor();

/**
 * React hook for resource monitoring
 */
export function useResourceMonitoring(
  enabled: boolean = true,
  intervalMs: number = 5000
) {
  const [metrics, setMetrics] = React.useState<ResourceMetrics | null>(null);
  const [alerts, setAlerts] = React.useState<ResourceAlert[]>([]);

  React.useEffect(() => {
    if (!enabled) {
      resourceMonitor.stopMonitoring();
      return;
    }

    const updateMetrics = async () => {
      const m = await resourceMonitor.getMetrics();
      setMetrics(m);
    };

    const handleAlert = (alert: ResourceAlert) => {
      setAlerts((prev) => [...prev, alert]);
    };

    // Initial metrics
    updateMetrics();

    // Start monitoring
    resourceMonitor.startMonitoring(intervalMs, handleAlert);

    // Update metrics in React state
    const metricsInterval = setInterval(updateMetrics, intervalMs);

    return () => {
      resourceMonitor.stopMonitoring();
      clearInterval(metricsInterval);
    };
  }, [enabled, intervalMs]);

  const clearAlerts = React.useCallback(() => {
    setAlerts([]);
    resourceMonitor.clearAlerts();
  }, []);

  return {
    metrics,
    alerts,
    clearAlerts,
  };
}

// For non-React usage
import * as React from 'react';
