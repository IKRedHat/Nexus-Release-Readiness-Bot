'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, Calendar, BarChart3, Activity, Settings,
  Users, Shield, Lightbulb, Zap, LogOut, Menu, X 
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import { ROUTES, PERMISSIONS } from '@/lib/constants';

interface LayoutProps {
  children: ReactNode;
}

interface NavItem {
  to: string;
  icon: any;
  label: string;
  permission?: string;
}

const mainNavItems: NavItem[] = [
  { to: ROUTES.HOME, icon: LayoutDashboard, label: 'Dashboard' },
  { to: ROUTES.RELEASES, icon: Calendar, label: 'Releases' },
  { to: ROUTES.METRICS, icon: BarChart3, label: 'Observability' },
  { to: ROUTES.HEALTH, icon: Activity, label: 'Health Monitor' },
  { to: ROUTES.FEATURE_REQUESTS, icon: Lightbulb, label: 'Feature Requests' },
  { to: ROUTES.SETTINGS, icon: Settings, label: 'Configuration' },
];

const adminNavItems: NavItem[] = [
  { to: ROUTES.ADMIN_USERS, icon: Users, label: 'User Management', permission: PERMISSIONS.USERS_VIEW },
  { to: ROUTES.ADMIN_ROLES, icon: Shield, label: 'Role Management', permission: PERMISSIONS.ROLES_VIEW },
];

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const pathname = usePathname();
  const { user, logout, hasPermission } = useAuth();

  const filteredAdminItems = adminNavItems.filter(item => 
    !item.permission || hasPermission(item.permission)
  );

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 h-full bg-card border-r border-border transition-all duration-300 z-50',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-border">
          {sidebarOpen ? (
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-emerald-600 flex items-center justify-center">
                <Zap className="w-6 h-6 text-background" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-foreground">Nexus</h1>
                <p className="text-xs text-muted-foreground">Admin Dashboard</p>
              </div>
            </div>
          ) : (
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-emerald-600 flex items-center justify-center mx-auto">
              <Zap className="w-6 h-6 text-background" />
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-accent rounded-lg"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {/* Main Navigation */}
          {mainNavItems.map((item) => {
            const isActive = pathname === item.to;
            return (
              <Link
                key={item.to}
                href={item.to}
                className={cn(
                  'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-foreground hover:bg-accent hover:text-accent-foreground'
                )}
                title={!sidebarOpen ? item.label : undefined}
              >
                <item.icon size={20} />
                {sidebarOpen && <span className="font-medium">{item.label}</span>}
              </Link>
            );
          })}

          {/* Admin Section */}
          {filteredAdminItems.length > 0 && (
            <>
              <div className="pt-4">
                {sidebarOpen && (
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-4 mb-2">
                    Administration
                  </p>
                )}
                <div className="border-t border-border mb-2" />
              </div>

              {filteredAdminItems.map((item) => {
                const isActive = pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    href={item.to}
                    className={cn(
                      'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-foreground hover:bg-accent hover:text-accent-foreground'
                    )}
                    title={!sidebarOpen ? item.label : undefined}
                  >
                    <item.icon size={20} />
                    {sidebarOpen && <span className="font-medium">{item.label}</span>}
                  </Link>
                );
              })}
            </>
          )}
        </nav>

        {/* User Section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border bg-card">
          {sidebarOpen ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-sm font-bold text-primary">
                    {user?.name?.charAt(0) || user?.email?.charAt(0) || '?'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">
                    {user?.name || 'User'}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">
                    {user?.email}
                  </p>
                </div>
              </div>
              <button
                onClick={logout}
                className="p-2 hover:bg-accent rounded-lg text-muted-foreground hover:text-foreground"
                title="Logout"
              >
                <LogOut size={18} />
              </button>
            </div>
          ) : (
            <button
              onClick={logout}
              className="w-full p-2 hover:bg-accent rounded-lg mx-auto flex justify-center"
              title="Logout"
            >
              <LogOut size={20} />
            </button>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main
        className={cn(
          'flex-1 transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-20'
        )}
      >
        {/* Header */}
        <header className="h-16 border-b border-border bg-card flex items-center justify-between px-8">
          <div>
            <p className="text-sm text-muted-foreground">
              Welcome back, {user?.name || 'User'}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-muted-foreground">System Healthy</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}

