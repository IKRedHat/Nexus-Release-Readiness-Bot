'use client';

import { ReactNode } from 'react';
import { Menu, X } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Props for Sidebar component
 */
export interface SidebarProps {
  /** Sidebar content (logo, nav, user profile) */
  children: ReactNode;
  /** Whether the sidebar is collapsed */
  collapsed?: boolean;
  /** Callback when toggle button is clicked */
  onToggle?: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Sidebar Component
 * 
 * Main container for the sidebar navigation.
 * Supports collapsed and expanded states.
 * 
 * @example
 * <Sidebar collapsed={isCollapsed} onToggle={() => setIsCollapsed(!isCollapsed)}>
 *   <SidebarLogo collapsed={isCollapsed} />
 *   <SidebarNav items={navItems} collapsed={isCollapsed} />
 *   <SidebarUserProfile user={user} collapsed={isCollapsed} />
 * </Sidebar>
 */
export function Sidebar({
  children,
  collapsed = false,
  onToggle,
  className,
}: SidebarProps) {
  return (
    <aside
      role="complementary"
      aria-label="Main navigation sidebar"
      className={cn(
        'fixed left-0 top-0 h-full bg-card border-r border-border transition-all duration-300 z-50 flex flex-col',
        collapsed ? 'w-20' : 'w-64',
        className
      )}
    >
      {/* Toggle Button */}
      <div className="absolute top-4 right-2">
        <button
          onClick={onToggle}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
        >
          {collapsed ? (
            <Menu size={20} className="text-muted-foreground" />
          ) : (
            <X size={20} className="text-muted-foreground" />
          )}
        </button>
      </div>

      {/* Content */}
      {children}
    </aside>
  );
}

