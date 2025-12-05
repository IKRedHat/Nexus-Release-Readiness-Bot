'use client';

import { ReactNode, useState, FormEvent } from 'react';
import Link from 'next/link';
import { Bell, Search, Sun, Moon, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { User } from '@/types';

/**
 * System status type
 */
export type SystemStatus = 'healthy' | 'degraded' | 'down';

/**
 * Breadcrumb item
 */
export interface BreadcrumbItem {
  label: string;
  href?: string;
}

/**
 * Props for AppHeader component
 */
export interface AppHeaderProps {
  /** Current user */
  user?: User | null;
  /** System status */
  systemStatus?: SystemStatus;
  /** Whether to show search */
  showSearch?: boolean;
  /** Search callback */
  onSearch?: (query: string) => void;
  /** Whether to show notifications */
  showNotifications?: boolean;
  /** Notification count */
  notificationCount?: number;
  /** Notification click callback */
  onNotificationClick?: () => void;
  /** Breadcrumb navigation */
  breadcrumbs?: BreadcrumbItem[];
  /** Custom actions to render */
  actions?: ReactNode;
  /** Whether to show theme toggle */
  showThemeToggle?: boolean;
  /** Theme toggle callback */
  onThemeToggle?: () => void;
  /** Current theme */
  theme?: 'light' | 'dark';
  /** Additional CSS classes */
  className?: string;
}

/**
 * Status indicator colors
 */
const statusColors: Record<SystemStatus, string> = {
  healthy: 'bg-green-500',
  degraded: 'bg-yellow-500',
  down: 'bg-red-500',
};

/**
 * AppHeader Component
 * 
 * Top navigation bar for the application.
 * Displays welcome message, system status, and optional features.
 * 
 * @example
 * <AppHeader 
 *   user={currentUser}
 *   systemStatus="healthy"
 *   showSearch
 *   showNotifications
 *   notificationCount={3}
 * />
 */
export function AppHeader({
  user,
  systemStatus = 'healthy',
  showSearch = false,
  onSearch,
  showNotifications = false,
  notificationCount = 0,
  onNotificationClick,
  breadcrumbs,
  actions,
  showThemeToggle = false,
  onThemeToggle,
  theme = 'dark',
  className,
}: AppHeaderProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearchSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSearch?.(searchQuery);
  };

  const displayNotificationCount = notificationCount > 99 ? '99+' : notificationCount.toString();

  return (
    <header
      role="banner"
      className={cn(
        'h-16 border-b border-border bg-card flex items-center justify-between px-8',
        className
      )}
    >
      {/* Left Side: Welcome message or Breadcrumbs */}
      <div className="flex items-center gap-4">
        {breadcrumbs && breadcrumbs.length > 0 ? (
          <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm">
            {breadcrumbs.map((crumb, index) => (
              <span key={index} className="flex items-center gap-2">
                {crumb.href ? (
                  <Link
                    href={crumb.href}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-foreground font-medium">{crumb.label}</span>
                )}
                {index < breadcrumbs.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                )}
              </span>
            ))}
          </nav>
        ) : (
          <div>
            <p className="text-sm text-muted-foreground">
              Welcome back, {user?.name || 'User'}
            </p>
          </div>
        )}
      </div>

      {/* Right Side: Status, Search, Notifications, Actions */}
      <div className="flex items-center gap-4">
        {/* Search */}
        {showSearch && (
          <form
            role="search"
            onSubmit={handleSearchSubmit}
            className="relative hidden md:block"
          >
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              type="search"
              role="searchbox"
              placeholder="Search..."
              aria-label="Search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-64"
            />
          </form>
        )}

        {/* System Status */}
        <div className="flex items-center gap-2 text-sm">
          <div
            data-testid="status-indicator"
            className={cn(
              'w-2 h-2 rounded-full animate-pulse',
              statusColors[systemStatus]
            )}
          />
          <span className="text-muted-foreground capitalize">
            {systemStatus === 'healthy' ? 'System Healthy' : `System ${systemStatus}`}
          </span>
        </div>

        {/* Theme Toggle */}
        {showThemeToggle && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onThemeToggle}
            aria-label="Toggle theme"
            title="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5" />
            ) : (
              <Moon className="w-5 h-5" />
            )}
          </Button>
        )}

        {/* Notifications */}
        {showNotifications && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onNotificationClick}
            aria-label="View notifications"
            title="Notifications"
            className="relative"
          >
            <Bell className="w-5 h-5" />
            {notificationCount > 0 && (
              <Badge
                className="absolute -top-1 -right-1 h-5 min-w-[20px] flex items-center justify-center text-xs px-1"
                variant="destructive"
              >
                {displayNotificationCount}
              </Badge>
            )}
          </Button>
        )}

        {/* Custom Actions */}
        {actions && (
          <div className="flex items-center gap-2">
            {actions}
          </div>
        )}
      </div>
    </header>
  );
}

