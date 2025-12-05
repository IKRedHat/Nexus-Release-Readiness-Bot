'use client';

import { ReactNode, useState } from 'react';
import { 
  LayoutDashboard, Calendar, BarChart3, Activity, Settings,
  Users, Shield, Lightbulb
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
];

/**
 * Layout Component
 * 
 * Main application layout that provides:
 * - Collapsible sidebar with navigation
 * - Header with user info and system status
 * - Main content area
 * 
 * Now uses modular sub-components:
 * - Sidebar, SidebarLogo, SidebarNav, SidebarUserProfile
 * - AppHeader
 * 
 * @example
 * <Layout>
 *   <PageContent />
 * </Layout>
 */
export default function Layout({ children }: LayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { user, logout, hasPermission } = useAuth();

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
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
      <main
        className={cn(
          'flex-1 transition-all duration-300',
          sidebarCollapsed ? 'ml-20' : 'ml-64'
        )}
      >
        {/* Header */}
        <AppHeader
          user={user}
          systemStatus="healthy"
        />

        {/* Page Content */}
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
