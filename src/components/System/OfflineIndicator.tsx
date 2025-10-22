import React, { useEffect, useState } from 'react';
import { WifiOff, Wifi, RefreshCw, AlertCircle } from 'lucide-react';
import { useConnectionStatus } from '../../hooks/useConnectionStatus';
import { ANIMATION } from '../../constants/ui';

export const OfflineIndicator: React.FC = () => {
  const { status, isOnline, error, forceCheck } = useConnectionStatus();
  const [isVisible, setIsVisible] = useState(false);
  const [wasOffline, setWasOffline] = useState(false);

  // Show/hide logic with animation
  useEffect(() => {
    if (!isOnline) {
      setIsVisible(true);
      setWasOffline(true);
    } else if (wasOffline) {
      // Show "Connected" message briefly before hiding
      const timer = setTimeout(() => {
        setIsVisible(false);
      }, 3000); // Show for 3 seconds then hide

      return () => clearTimeout(timer);
    }
  }, [isOnline, wasOffline]);

  // Don't render anything if we've never been offline and are currently online
  if (!isVisible) {
    return null;
  }

  const getStatusConfig = () => {
    switch (status) {
      case 'offline':
        return {
          icon: WifiOff,
          bgColor: 'bg-error-500',
          textColor: 'text-white',
          message: 'Connection Lost',
          description: error || 'Unable to reach backend server',
          showRetry: true,
        };
      case 'reconnecting':
        return {
          icon: RefreshCw,
          bgColor: 'bg-warning-500',
          textColor: 'text-white',
          message: 'Reconnecting...',
          description: 'Attempting to restore connection',
          showRetry: false,
        };
      case 'online':
        return {
          icon: Wifi,
          bgColor: 'bg-success-500',
          textColor: 'text-white',
          message: 'Connected',
          description: 'Connection restored successfully',
          showRetry: false,
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-[100] animate-in slide-in-from-top duration-300`}
      role="alert"
      aria-live="assertive"
    >
      {/* Banner */}
      <div className={`${config.bgColor} ${config.textColor} shadow-lg`}>
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between gap-4">
            {/* Left: Icon + Message */}
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {/* Icon */}
              <div className="flex-shrink-0">
                <Icon
                  size={20}
                  className={status === 'reconnecting' ? 'animate-spin' : ''}
                  aria-hidden="true"
                />
              </div>

              {/* Message */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-sm">
                    {config.message}
                  </p>
                  {status === 'offline' && (
                    <AlertCircle size={16} aria-hidden="true" />
                  )}
                </div>
                <p className="text-xs opacity-90 mt-0.5">
                  {config.description}
                </p>
              </div>
            </div>

            {/* Right: Retry Button */}
            {config.showRetry && (
              <button
                onClick={forceCheck}
                className="flex-shrink-0 px-3 py-1.5 text-xs font-medium bg-white/20 hover:bg-white/30
                         rounded-lg transition-all duration-150 active:scale-95
                         focus:outline-none focus:ring-2 focus:ring-white/50"
                aria-label="Retry connection"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Overlay for offline state - prevents interaction */}
      {!isOnline && (
        <div
          className="fixed inset-0 bg-neutral-900/10 backdrop-blur-[1px] pointer-events-none z-[99]"
          aria-hidden="true"
        />
      )}
    </div>
  );
};
