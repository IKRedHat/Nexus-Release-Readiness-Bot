/**
 * Notifications Center Component
 * 
 * A dropdown notification center that displays persistent notifications.
 * Different from toasts - these are stored and can be reviewed.
 */

'use client';

import { useState, useCallback, createContext, useContext, ReactNode } from 'react';
import { Bell, Check, X, Info, AlertTriangle, AlertCircle, CheckCircle } from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { Button } from './button';
import { cn } from '@/lib/utils';

// =============================================================================
// Types
// =============================================================================

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface NotificationsContextType {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

// =============================================================================
// Context
// =============================================================================

const NotificationsContext = createContext<NotificationsContextType | undefined>(undefined);

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const addNotification = useCallback(
    (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
      const newNotification: Notification = {
        ...notification,
        id: `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
        read: false,
      };

      setNotifications((prev) => [newNotification, ...prev].slice(0, 50)); // Keep last 50
    },
    []
  );

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  return (
    <NotificationsContext.Provider
      value={{
        notifications,
        unreadCount,
        addNotification,
        markAsRead,
        markAllAsRead,
        removeNotification,
        clearAll,
      }}
    >
      {children}
    </NotificationsContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationsContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationsProvider');
  }
  return context;
}

// =============================================================================
// Icons
// =============================================================================

const typeIcons: Record<NotificationType, React.ElementType> = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertCircle,
};

const typeColors: Record<NotificationType, string> = {
  info: 'text-blue-500',
  success: 'text-green-500',
  warning: 'text-yellow-500',
  error: 'text-red-500',
};

// =============================================================================
// Component
// =============================================================================

interface NotificationsCenterProps {
  className?: string;
}

export function NotificationsCenter({ className }: NotificationsCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
  } = useNotifications();

  return (
    <div className={cn('relative', className)}>
      {/* Trigger Button */}
      <Button
        variant="ghost"
        size="icon"
        className="relative h-9 w-9"
        onClick={() => setIsOpen(!isOpen)}
        title="Notifications"
      >
        <Bell className="h-5 w-5 text-muted-foreground" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-destructive text-destructive-foreground text-xs flex items-center justify-center font-medium">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Panel */}
          <div className="absolute right-0 top-full mt-2 z-50 w-80 sm:w-96 bg-popover border border-border rounded-lg shadow-lg overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/50">
              <h3 className="font-semibold">Notifications</h3>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs"
                    onClick={markAllAsRead}
                  >
                    <Check className="h-3 w-3 mr-1" />
                    Mark all read
                  </Button>
                )}
                {notifications.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs text-destructive hover:text-destructive"
                    onClick={clearAll}
                  >
                    Clear all
                  </Button>
                )}
              </div>
            </div>

            {/* Content */}
            <div className="max-h-[400px] overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="py-8 text-center text-muted-foreground">
                  <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No notifications</p>
                </div>
              ) : (
                <ul className="divide-y divide-border">
                  {notifications.map((notification) => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onRead={() => markAsRead(notification.id)}
                      onRemove={() => removeNotification(notification.id)}
                    />
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// =============================================================================
// Notification Item
// =============================================================================

interface NotificationItemProps {
  notification: Notification;
  onRead: () => void;
  onRemove: () => void;
}

function NotificationItem({ notification, onRead, onRemove }: NotificationItemProps) {
  const Icon = typeIcons[notification.type];
  const colorClass = typeColors[notification.type];

  return (
    <li
      className={cn(
        'px-4 py-3 hover:bg-muted/50 transition-colors',
        !notification.read && 'bg-accent/50'
      )}
      onClick={onRead}
    >
      <div className="flex gap-3">
        <Icon className={cn('h-5 w-5 flex-shrink-0 mt-0.5', colorClass)} />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={cn('text-sm font-medium', !notification.read && 'font-semibold')}>
              {notification.title}
            </p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              className="text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{notification.message}</p>
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-muted-foreground">
              {formatDistanceToNow(notification.timestamp, { addSuffix: true })}
            </span>
            {notification.action && (
              <Button
                variant="link"
                size="sm"
                className="h-auto p-0 text-xs"
                onClick={(e) => {
                  e.stopPropagation();
                  notification.action?.onClick();
                }}
              >
                {notification.action.label}
              </Button>
            )}
          </div>
        </div>
      </div>
    </li>
  );
}

export default NotificationsCenter;

