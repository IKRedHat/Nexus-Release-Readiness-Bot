/**
 * Connection Status Component
 * 
 * Displays real-time connection status for WebSocket connections.
 */

'use client';

import { Wifi, WifiOff, RefreshCw, Loader2 } from 'lucide-react';
import { Button } from './button';
import { cn } from '@/lib/utils';

export type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'error';

interface ConnectionStatusProps {
  status: ConnectionState;
  latency?: number | null;
  onReconnect?: () => void;
  className?: string;
  showLatency?: boolean;
  compact?: boolean;
}

const statusConfig: Record<ConnectionState, {
  icon: React.ElementType;
  label: string;
  color: string;
  bgColor: string;
  animate?: boolean;
}> = {
  connected: {
    icon: Wifi,
    label: 'Connected',
    color: 'text-green-500',
    bgColor: 'bg-green-500',
  },
  connecting: {
    icon: Loader2,
    label: 'Connecting',
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500',
    animate: true,
  },
  disconnected: {
    icon: WifiOff,
    label: 'Disconnected',
    color: 'text-muted-foreground',
    bgColor: 'bg-muted-foreground',
  },
  error: {
    icon: WifiOff,
    label: 'Error',
    color: 'text-red-500',
    bgColor: 'bg-red-500',
  },
};

export function ConnectionStatus({
  status,
  latency,
  onReconnect,
  className,
  showLatency = true,
  compact = false,
}: ConnectionStatusProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  if (compact) {
    return (
      <div
        className={cn('flex items-center gap-1.5', className)}
        title={`${config.label}${latency ? ` (${latency}ms)` : ''}`}
      >
        <div className={cn('w-2 h-2 rounded-full', config.bgColor, status === 'connected' && 'animate-pulse')} />
        {showLatency && latency && (
          <span className="text-xs text-muted-foreground">{latency}ms</span>
        )}
      </div>
    );
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Icon
        className={cn(
          'w-4 h-4',
          config.color,
          config.animate && 'animate-spin'
        )}
      />
      <span className={cn('text-sm', config.color)}>{config.label}</span>
      
      {showLatency && latency && status === 'connected' && (
        <span className="text-xs text-muted-foreground">({latency}ms)</span>
      )}
      
      {(status === 'disconnected' || status === 'error') && onReconnect && (
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2"
          onClick={onReconnect}
        >
          <RefreshCw className="w-3 h-3 mr-1" />
          Retry
        </Button>
      )}
    </div>
  );
}

export default ConnectionStatus;

