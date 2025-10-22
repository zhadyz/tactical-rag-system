import React, { useState } from 'react';
import { Activity, AlertTriangle, CheckCircle, XCircle, HardDrive, Cpu, Zap } from 'lucide-react';
import { useResourceMonitoring } from '../../utils/resourceMonitor';
import { useAutoRecovery, type HealthCheckResult } from '../../services/autoRecovery';

interface SystemHealthIndicatorProps {
  position?: 'top-right' | 'bottom-right' | 'bottom-left';
  enableResourceMonitoring?: boolean;
  enableAutoRecovery?: boolean;
}

export const SystemHealthIndicator: React.FC<SystemHealthIndicatorProps> = ({
  position = 'bottom-right',
  enableResourceMonitoring = true,
  enableAutoRecovery = true,
}) => {
  const [expanded, setExpanded] = useState(false);

  const { metrics, alerts, clearAlerts } = useResourceMonitoring(
    enableResourceMonitoring,
    10000
  );

  const { healthStatus, recoveryActions } = useAutoRecovery(enableAutoRecovery, {
    healthCheckInterval: 10000,
    maxConsecutiveFailures: 3,
    enableAutoReload: false,
  });

  const getHealthStatusColor = (status: HealthCheckResult['status']) => {
    switch (status) {
      case 'healthy':
        return 'text-green-500';
      case 'degraded':
        return 'text-yellow-500';
      case 'down':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getHealthStatusIcon = (status: HealthCheckResult['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle size={16} />;
      case 'degraded':
        return <AlertTriangle size={16} />;
      case 'down':
        return <XCircle size={16} />;
      default:
        return <Activity size={16} />;
    }
  };

  const positionClasses = {
    'top-right': 'top-4 right-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
  };

  const hasActiveAlerts = alerts.length > 0 || healthStatus.status !== 'healthy';

  return (
    <div className={`fixed ${positionClasses[position]} z-50`}>
      {/* Compact indicator */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={`p-2 rounded-lg shadow-lg transition-all ${
          hasActiveAlerts
            ? 'bg-yellow-100 dark:bg-yellow-900/30 border-2 border-yellow-500 animate-pulse'
            : 'bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700'
        }`}
        title="System Health"
      >
        <div className={`flex items-center gap-2 ${getHealthStatusColor(healthStatus.status)}`}>
          {getHealthStatusIcon(healthStatus.status)}
          {hasActiveAlerts && (
            <span className="text-xs font-semibold">{alerts.length}</span>
          )}
        </div>
      </button>

      {/* Expanded panel */}
      {expanded && (
        <div className="absolute bottom-full right-0 mb-2 w-96 bg-white dark:bg-neutral-800 rounded-xl shadow-2xl border border-neutral-200 dark:border-neutral-700 overflow-hidden">
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-primary-600 to-primary-700 text-white">
            <div className="flex items-center gap-3">
              <Activity size={20} />
              <div>
                <h3 className="font-semibold text-sm">System Health</h3>
                <p className="text-xs text-primary-100">
                  Real-time monitoring
                </p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
            {/* Backend Health */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-neutral-600 dark:text-neutral-400 uppercase">
                Backend Status
              </h4>
              <div className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-900 rounded-lg">
                <div className="flex items-center gap-2">
                  {getHealthStatusIcon(healthStatus.status)}
                  <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                    {healthStatus.status === 'healthy' && 'Healthy'}
                    {healthStatus.status === 'degraded' && 'Degraded'}
                    {healthStatus.status === 'down' && 'Down'}
                  </span>
                </div>
                <div className="text-xs text-neutral-500 dark:text-neutral-400">
                  {healthStatus.latency.toFixed(0)}ms
                </div>
              </div>
              {healthStatus.consecutiveFailures > 0 && (
                <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                  {healthStatus.consecutiveFailures} consecutive failures
                </div>
              )}
            </div>

            {/* Resource Metrics */}
            {metrics && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-neutral-600 dark:text-neutral-400 uppercase">
                  Resources
                </h4>

                {/* Memory */}
                {metrics.memory.total > 0 && (
                  <div className="p-3 bg-neutral-50 dark:bg-neutral-900 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Cpu size={14} className="text-neutral-500" />
                        <span className="text-xs font-medium text-neutral-900 dark:text-neutral-100">
                          Memory
                        </span>
                      </div>
                      <span className="text-xs text-neutral-500 dark:text-neutral-400">
                        {metrics.memory.percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full transition-all ${
                          metrics.memory.percentage > 90
                            ? 'bg-red-500'
                            : metrics.memory.percentage > 70
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{ width: `${metrics.memory.percentage}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Storage */}
                {metrics.storage && (
                  <div className="p-3 bg-neutral-50 dark:bg-neutral-900 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <HardDrive size={14} className="text-neutral-500" />
                        <span className="text-xs font-medium text-neutral-900 dark:text-neutral-100">
                          Storage
                        </span>
                      </div>
                      <span className="text-xs text-neutral-500 dark:text-neutral-400">
                        {metrics.storage.percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full transition-all ${
                          metrics.storage.percentage > 95
                            ? 'bg-red-500'
                            : metrics.storage.percentage > 80
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{ width: `${metrics.storage.percentage}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* FPS */}
                <div className="p-3 bg-neutral-50 dark:bg-neutral-900 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Zap size={14} className="text-neutral-500" />
                      <span className="text-xs font-medium text-neutral-900 dark:text-neutral-100">
                        Performance
                      </span>
                    </div>
                    <span className="text-xs text-neutral-500 dark:text-neutral-400">
                      {metrics.performance.fps} FPS
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Active Alerts */}
            {alerts.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-neutral-600 dark:text-neutral-400 uppercase">
                    Alerts
                  </h4>
                  <button
                    onClick={clearAlerts}
                    className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
                  >
                    Clear
                  </button>
                </div>
                {alerts.map((alert, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border ${
                      alert.level === 'error'
                        ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                        : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <AlertTriangle
                        size={14}
                        className={
                          alert.level === 'error'
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-yellow-600 dark:text-yellow-400'
                        }
                      />
                      <div className="flex-1">
                        <p className="text-xs font-medium text-neutral-900 dark:text-neutral-100">
                          {alert.message}
                        </p>
                        <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1">
                          Threshold: {alert.threshold}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Recent Recovery Actions */}
            {recoveryActions.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-neutral-600 dark:text-neutral-400 uppercase">
                  Recovery Log
                </h4>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {recoveryActions.slice(-5).reverse().map((action, idx) => (
                    <div
                      key={idx}
                      className="text-xs p-2 bg-neutral-50 dark:bg-neutral-900 rounded"
                    >
                      <span className={action.success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                        {action.type}
                      </span>
                      : {action.reason}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-3 bg-neutral-50 dark:bg-neutral-900 border-t border-neutral-200 dark:border-neutral-700">
            <p className="text-xs text-center text-neutral-500 dark:text-neutral-400">
              Field deployment monitoring active
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
