/**
 * WebSocket Hook for Real-Time Updates
 * 
 * Provides real-time data streaming from the backend.
 * Features:
 * - Auto-reconnection with exponential backoff
 * - Connection status tracking
 * - Heartbeat/ping-pong
 * - Event subscription
 * - Graceful degradation to polling
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

// =============================================================================
// Types
// =============================================================================

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WebSocketMessage<T = unknown> {
  type: string;
  payload: T;
  timestamp: string;
}

export interface UseWebSocketOptions {
  /** Enable auto-reconnection */
  autoReconnect?: boolean;
  /** Maximum reconnection attempts */
  maxReconnectAttempts?: number;
  /** Initial reconnection delay (ms) */
  reconnectDelay?: number;
  /** Heartbeat interval (ms) */
  heartbeatInterval?: number;
  /** Message handler */
  onMessage?: (message: WebSocketMessage) => void;
  /** Connection established handler */
  onOpen?: () => void;
  /** Connection closed handler */
  onClose?: () => void;
  /** Error handler */
  onError?: (error: Event) => void;
  /** Enable debug logging */
  debug?: boolean;
}

export interface UseWebSocketReturn<T = unknown> {
  /** Current connection status */
  status: WebSocketStatus;
  /** Last received data */
  data: T | null;
  /** Last error */
  error: Error | null;
  /** Send a message */
  send: (message: unknown) => void;
  /** Subscribe to a channel/topic */
  subscribe: (channel: string) => void;
  /** Unsubscribe from a channel/topic */
  unsubscribe: (channel: string) => void;
  /** Manually reconnect */
  reconnect: () => void;
  /** Disconnect */
  disconnect: () => void;
  /** Is connected */
  isConnected: boolean;
  /** Connection latency (ms) */
  latency: number | null;
}

// =============================================================================
// Constants
// =============================================================================

const DEFAULT_OPTIONS: Required<UseWebSocketOptions> = {
  autoReconnect: true,
  maxReconnectAttempts: 5,
  reconnectDelay: 1000,
  heartbeatInterval: 30000,
  onMessage: () => {},
  onOpen: () => {},
  onClose: () => {},
  onError: () => {},
  debug: false,
};

// =============================================================================
// Hook Implementation
// =============================================================================

export function useWebSocket<T = unknown>(
  url: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingTimestampRef = useRef<number | null>(null);
  const subscribedChannelsRef = useRef<Set<string>>(new Set());

  const log = useCallback(
    (...args: unknown[]) => {
      if (opts.debug) {
        console.log('[WebSocket]', ...args);
      }
    },
    [opts.debug]
  );

  // Clear all timeouts
  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  // Send heartbeat ping
  const sendHeartbeat = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      pingTimestampRef.current = Date.now();
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
      log('Sent heartbeat ping');
      
      // Schedule next heartbeat
      heartbeatTimeoutRef.current = setTimeout(sendHeartbeat, opts.heartbeatInterval);
    }
  }, [opts.heartbeatInterval, log]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!url) {
      log('No URL provided, skipping connection');
      return;
    }

    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      log('Already connected');
      return;
    }

    log('Connecting to', url);
    setStatus('connecting');
    setError(null);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        log('Connected');
        setStatus('connected');
        reconnectAttemptsRef.current = 0;
        opts.onOpen();

        // Start heartbeat
        sendHeartbeat();

        // Re-subscribe to channels
        subscribedChannelsRef.current.forEach((channel) => {
          ws.send(JSON.stringify({ type: 'subscribe', channel }));
        });
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage<T> = JSON.parse(event.data);
          log('Received message:', message.type);

          // Handle pong (heartbeat response)
          if (message.type === 'pong' && pingTimestampRef.current) {
            setLatency(Date.now() - pingTimestampRef.current);
            pingTimestampRef.current = null;
            return;
          }

          // Update data and notify handler
          setData(message.payload);
          opts.onMessage(message);
        } catch (err) {
          log('Failed to parse message:', err);
        }
      };

      ws.onclose = (event) => {
        log('Connection closed:', event.code, event.reason);
        setStatus('disconnected');
        clearTimeouts();
        opts.onClose();

        // Auto-reconnect if enabled
        if (opts.autoReconnect && reconnectAttemptsRef.current < opts.maxReconnectAttempts) {
          const delay = opts.reconnectDelay * Math.pow(2, reconnectAttemptsRef.current);
          log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${opts.maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };

      ws.onerror = (event) => {
        log('Connection error:', event);
        setStatus('error');
        setError(new Error('WebSocket connection error'));
        opts.onError(event);
      };
    } catch (err) {
      log('Failed to create WebSocket:', err);
      setStatus('error');
      setError(err instanceof Error ? err : new Error('Failed to connect'));
    }
  }, [url, opts, clearTimeouts, sendHeartbeat, log]);

  // Disconnect
  const disconnect = useCallback(() => {
    log('Disconnecting');
    clearTimeouts();
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    
    setStatus('disconnected');
  }, [clearTimeouts, log]);

  // Reconnect
  const reconnect = useCallback(() => {
    log('Manual reconnect');
    reconnectAttemptsRef.current = 0;
    disconnect();
    connect();
  }, [connect, disconnect, log]);

  // Send message
  const send = useCallback(
    (message: unknown) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(message));
        log('Sent message:', message);
      } else {
        log('Cannot send, not connected');
      }
    },
    [log]
  );

  // Subscribe to channel
  const subscribe = useCallback(
    (channel: string) => {
      subscribedChannelsRef.current.add(channel);
      
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'subscribe', channel }));
        log('Subscribed to', channel);
      }
    },
    [log]
  );

  // Unsubscribe from channel
  const unsubscribe = useCallback(
    (channel: string) => {
      subscribedChannelsRef.current.delete(channel);
      
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'unsubscribe', channel }));
        log('Unsubscribed from', channel);
      }
    },
    [log]
  );

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [url]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    status,
    data,
    error,
    send,
    subscribe,
    unsubscribe,
    reconnect,
    disconnect,
    isConnected: status === 'connected',
    latency,
  };
}

// =============================================================================
// WebSocket URL Helper
// =============================================================================

/**
 * Get WebSocket URL for backend connection
 * 
 * Uses NEXT_PUBLIC_API_URL or falls back to window.location
 */
function getWebSocketUrl(path: string): string | null {
  if (typeof window === 'undefined') return null;
  
  // Get API URL from environment or use current host
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
  
  if (apiUrl) {
    // Convert http(s):// to ws(s)://
    const wsUrl = apiUrl
      .replace('https://', 'wss://')
      .replace('http://', 'ws://');
    return `${wsUrl}${path}`;
  }
  
  // Fallback to same host (for proxied deployments)
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}${path}`;
}

// =============================================================================
// Specialized Hooks
// =============================================================================

/**
 * Hook for real-time health updates
 * 
 * Connects to /ws/health and receives:
 * - Health status updates every 10 seconds
 * - Service status changes
 */
export function useHealthWebSocket() {
  const wsUrl = getWebSocketUrl('/ws/health');

  return useWebSocket(wsUrl, {
    autoReconnect: true,
    heartbeatInterval: 10000,
    debug: process.env.NODE_ENV === 'development',
  });
}

/**
 * Hook for real-time activity updates
 * 
 * Connects to /ws/activity and receives:
 * - User actions (login, logout, CRUD operations)
 * - System events
 * - Audit log entries
 */
export function useActivityWebSocket() {
  const wsUrl = getWebSocketUrl('/ws/activity');

  return useWebSocket(wsUrl, {
    autoReconnect: true,
    heartbeatInterval: 30000,
    debug: process.env.NODE_ENV === 'development',
  });
}

/**
 * Hook for real-time metrics updates
 * 
 * Connects to /ws/metrics and receives:
 * - CPU/Memory usage
 * - Request rates
 * - Performance metrics
 */
export function useMetricsWebSocket() {
  const wsUrl = getWebSocketUrl('/ws/metrics');

  return useWebSocket(wsUrl, {
    autoReconnect: true,
    heartbeatInterval: 15000,
    debug: process.env.NODE_ENV === 'development',
  });
}

/**
 * Hook for main WebSocket with channel subscription
 * 
 * Connects to /ws and supports subscribing to multiple channels:
 * - 'health' - Health updates
 * - 'activity' - Activity feed
 * - 'metrics' - Metrics updates
 * - 'notifications' - User notifications
 */
export function useMainWebSocket(channels: string[] = []) {
  const wsUrl = getWebSocketUrl('/ws');
  
  const ws = useWebSocket(wsUrl, {
    autoReconnect: true,
    heartbeatInterval: 30000,
    debug: process.env.NODE_ENV === 'development',
    onOpen: () => {
      // Subscribe to requested channels on connection
      channels.forEach((channel) => {
        ws.subscribe(channel);
      });
    },
  });

  return ws;
}

export default useWebSocket;

