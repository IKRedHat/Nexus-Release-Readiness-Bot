/**
 * WebSocket Provider
 * 
 * Global WebSocket connection management with multiple channels.
 * Provides real-time updates throughout the application.
 */

'use client';

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { useWebSocket, WebSocketStatus, WebSocketMessage } from '@/hooks/useWebSocket';

// =============================================================================
// Types
// =============================================================================

export interface RealtimeEvent {
  type: 'health_update' | 'release_update' | 'activity' | 'notification' | 'metrics_update';
  payload: unknown;
  timestamp: string;
}

interface WebSocketContextValue {
  /** Connection status */
  status: WebSocketStatus;
  /** Is connected */
  isConnected: boolean;
  /** Connection latency */
  latency: number | null;
  /** Last health update */
  healthData: unknown | null;
  /** Last activity update */
  activityData: unknown | null;
  /** Last metrics update */
  metricsData: unknown | null;
  /** Subscribe to event type */
  subscribe: (eventType: string, callback: (data: unknown) => void) => () => void;
  /** Send message */
  send: (message: unknown) => void;
  /** Reconnect */
  reconnect: () => void;
}

// =============================================================================
// Context
// =============================================================================

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

// =============================================================================
// Provider
// =============================================================================

interface WebSocketProviderProps {
  children: ReactNode;
  /** Base WebSocket URL (optional, auto-detected if not provided) */
  baseUrl?: string;
  /** Enable WebSocket connection */
  enabled?: boolean;
}

export function WebSocketProvider({ 
  children, 
  baseUrl,
  enabled = true 
}: WebSocketProviderProps) {
  const [healthData, setHealthData] = useState<unknown | null>(null);
  const [activityData, setActivityData] = useState<unknown | null>(null);
  const [metricsData, setMetricsData] = useState<unknown | null>(null);
  const [subscribers] = useState(() => new Map<string, Set<(data: unknown) => void>>());

  // Determine WebSocket URL
  const wsUrl = enabled && typeof window !== 'undefined'
    ? baseUrl || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`
    : null;

  // Handle incoming messages
  const handleMessage = useCallback((message: WebSocketMessage) => {
    const { type, payload } = message;

    // Update local state based on message type
    switch (type) {
      case 'health_update':
        setHealthData(payload);
        break;
      case 'activity':
        setActivityData(payload);
        break;
      case 'metrics_update':
        setMetricsData(payload);
        break;
    }

    // Notify subscribers
    const callbacks = subscribers.get(type);
    if (callbacks) {
      callbacks.forEach((callback) => callback(payload));
    }

    // Also notify wildcard subscribers
    const wildcardCallbacks = subscribers.get('*');
    if (wildcardCallbacks) {
      wildcardCallbacks.forEach((callback) => callback(message));
    }
  }, [subscribers]);

  // Use WebSocket hook
  const {
    status,
    isConnected,
    latency,
    send,
    reconnect,
    subscribe: wsSubscribe,
  } = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    autoReconnect: true,
    debug: process.env.NODE_ENV === 'development',
  });

  // Subscribe to channels on connect
  useEffect(() => {
    if (isConnected) {
      wsSubscribe('health');
      wsSubscribe('activity');
      wsSubscribe('metrics');
      wsSubscribe('notifications');
    }
  }, [isConnected, wsSubscribe]);

  // Subscribe to event types
  const subscribe = useCallback(
    (eventType: string, callback: (data: unknown) => void) => {
      if (!subscribers.has(eventType)) {
        subscribers.set(eventType, new Set());
      }
      subscribers.get(eventType)!.add(callback);

      // Return unsubscribe function
      return () => {
        subscribers.get(eventType)?.delete(callback);
      };
    },
    [subscribers]
  );

  const value: WebSocketContextValue = {
    status,
    isConnected,
    latency,
    healthData,
    activityData,
    metricsData,
    subscribe,
    send,
    reconnect,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

// =============================================================================
// Hook
// =============================================================================

export function useRealtimeContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useRealtimeContext must be used within WebSocketProvider');
  }
  return context;
}

/**
 * Hook to subscribe to specific realtime events
 */
export function useRealtimeEvent<T = unknown>(
  eventType: string,
  callback: (data: T) => void
) {
  const { subscribe } = useRealtimeContext();

  useEffect(() => {
    return subscribe(eventType, callback as (data: unknown) => void);
  }, [eventType, callback, subscribe]);
}

export default WebSocketProvider;

