'use client';

import { ReactNode, useState, useCallback } from 'react';
import { 
  LayoutDashboard, Calendar, BarChart3, Activity, Settings,
  Users, Shield, Lightbulb, ScrollText
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import { ROUTES, PERMISSIONS } from '@/lib/constants';

// Import modular components
import { Sidebar } from './layout/Sidebar';
import { SidebarLogo } from './layout/SidebarLogo';
import { SidebarNav, NavItem } from './layout/SidebarNav';
import { SidebarUserProfile } from './layout/SidebarUserProfile';
import { AppHeader } from './layout/AppHeader';

// Import new UI components
import { ThemeToggle } from './ui/theme-toggle';
import { NotificationsCenter } from './ui/notifications-center';
import { Breadcrumbs } from './ui/breadcrumbs';
import { MainContent } from './ui/skip-link';
import { ConnectionStatus } from './ui/connection-status';

// Import WebSocket hooks
import { useRealtimeContext } from '@/providers/WebSocketProvider';

interface LayoutProps {
  children: ReactNode;
}

/**
 * Main navigation items
 */
const mainNavItems: NavItem[] = [
  { to: ROUTES.HOME, icon: LayoutDashboard, label: 'Dashboard' },
  { to: ROUTES.RELEASES, icon: Calendar, label: 'Releases' },
  { to: ROUTES.METRICS, icon: BarChart3, label: 'Observability' },
  { to: ROUTES.HEALTH, icon: Activity, label: 'Health Monitor' },
  { to: ROUTES.FEATURE_REQUESTS, icon: Lightbulb, label: 'Feature Requests' },
  { to: ROUTES.SETTINGS, icon: Settings, label: 'Configuration' },
];

/**
 * Admin navigation items (requires permissions)
 */
const adminNavItems: NavItem[] = [
  { to: ROUTES.ADMIN_USERS, icon: Users, label: 'User Management', permission: PERMISSIONS.USERS_VIEW },
  { to: ROUTES.ADMIN_ROLES, icon: Shield, label: 'Role Management', permission: PERMISSIONS.ROLES_VIEW },
  { to: ROUTES.AUDIT_LOG, icon: ScrollText, label: 'Audit Log', permission: PERMISSIONS.AUDIT_VIEW },
];

/**
 * Layout Component
 * 
 * Main application layout that provides:
 * - Collapsible sidebar with navigation
 * - Header with user info, system status, theme toggle, and notifications
 * - Breadcrumbs navigation
 * - Main content area with skip-link target
 * 
 * Features:
 * - Theme switching (dark/light mode)
 * - Notifications center
 * - Breadcrumb navigation
 * - Keyboard shortcut for sidebar toggle (Cmd+B)
 * 
 * @example
 * <Layout>
 *   <PageContent />
 * </Layout>
 */
/**
 * Inner layout component that uses WebSocket context
 */
function LayoutContent({ children }: LayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { user, logout, hasPermission } = useAuth();
  
  // Get WebSocket connection status
  let wsStatus: 'connected' | 'connecting' | 'disconnected' | 'error' = 'disconnected';
  let wsLatency: number | null = null;
  let wsReconnect: (() => void) | undefined;
  
  try {
    const ws = useRealtimeContext();
    wsStatus = ws.status;
    wsLatency = ws.latency;
    wsReconnect = ws.reconnect;
  } catch {
    // WebSocket context not available (e.g., not wrapped in provider)
    wsStatus = 'disconnected';
  }

  // Toggle sidebar - exposed for keyboard shortcut
  const handleToggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => !prev);
  }, []);

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={handleToggleSidebar}
      >
        {/* Logo */}
        <SidebarLogo collapsed={sidebarCollapsed} />

        {/* Main Navigation */}
        <SidebarNav
          items={mainNavItems}
          collapsed={sidebarCollapsed}
        />

        {/* Admin Section Divider */}
        <div className="px-4 pt-2">
          <div className="border-t border-border" />
        </div>

        {/* Admin Navigation */}
        <SidebarNav
          items={adminNavItems}
          collapsed={sidebarCollapsed}
          title="Administration"
          hasPermission={hasPermission}
          className="pt-2"
        />

        {/* User Profile (positioned at bottom via CSS in component) */}
        <SidebarUserProfile
          user={user}
          onLogout={logout}
          collapsed={sidebarCollapsed}
        />
      </Sidebar>

      {/* Main Content */}
      <div
        className={cn(
          'flex-1 flex flex-col transition-all duration-300',
          sidebarCollapsed ? 'ml-20' : 'ml-64'
        )}
      >
        {/* Header */}
        <header
          role="banner"
          className="h-16 border-b border-border bg-card flex items-center justify-between px-8 sticky top-0 z-40"
        >
          {/* Left Side: Breadcrumbs */}
          <div className="flex items-center gap-4">
            <Breadcrumbs showHome />
          </div>

          {/* Right Side: Status, Theme, Notifications */}
          <div className="flex items-center gap-3">
            {/* Real-time Connection Status */}
            <ConnectionStatus
              status={wsStatus}
              latency={wsLatency}
              onReconnect={wsReconnect}
              compact
              showLatency
              className="hidden sm:flex mr-2"
            />

            {/* Theme Toggle */}
            <ThemeToggle />

            {/* Notifications */}
            <NotificationsCenter />

            {/* User Info (condensed) */}
            {user && (
              <div className="hidden lg:flex items-center gap-2 pl-3 border-l border-border">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-sm font-medium text-primary">
                    {user.name?.charAt(0) || 'U'}
                  </span>
                </div>
                <span className="text-sm text-muted-foreground">{user.name}</span>
              </div>
            )}
          </div>
        </header>

        {/* Page Content - with skip-link target */}
        <MainContent className="flex-1 p-8">
          {children}
        </MainContent>
      </div>
    </div>
  );
}

/**
 * Layout Component
 * 
 * Main application layout with WebSocket context awareness.
 * Wraps the inner LayoutContent which handles WebSocket connection display.
 */
export default function Layout({ children }: LayoutProps) {
  return <LayoutContent>{children}</LayoutContent>;
}
