'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Navigation item definition
 */
export interface NavItem {
  /** Route path */
  to: string;
  /** Lucide icon component */
  icon: LucideIcon | (() => JSX.Element);
  /** Display label */
  label: string;
  /** Required permission (optional) */
  permission?: string;
}

/**
 * Props for SidebarNav component
 */
export interface SidebarNavProps {
  /** Navigation items to display */
  items: NavItem[];
  /** Whether the sidebar is collapsed */
  collapsed?: boolean;
  /** Section title (optional) */
  title?: string;
  /** Function to check if user has permission */
  hasPermission?: (permission: string) => boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * SidebarNav Component
 * 
 * Displays navigation items in the sidebar.
 * Supports permission-based filtering and collapsed state.
 * 
 * @example
 * const items = [
 *   { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
 *   { to: '/releases', icon: Calendar, label: 'Releases' },
 * ];
 * 
 * <SidebarNav items={items} collapsed={isCollapsed} />
 */
export function SidebarNav({
  items,
  collapsed = false,
  title,
  hasPermission = () => true,
  className,
}: SidebarNavProps) {
  const pathname = usePathname();

  // Filter items based on permissions
  const filteredItems = items.filter((item) => {
    if (!item.permission) return true;
    return hasPermission(item.permission);
  });

  if (filteredItems.length === 0) return null;

  return (
    <nav
      role="navigation"
      aria-label={title || 'Main navigation'}
      className={cn('p-4 space-y-2', className)}
    >
      {/* Section Title */}
      {title && (
        <div
          className={cn(
            'text-xs font-semibold text-muted-foreground uppercase tracking-wider px-4 mb-2',
            collapsed && 'sr-only'
          )}
        >
          {title}
        </div>
      )}

      {/* Navigation Items */}
      {filteredItems.map((item) => {
        const isActive = pathname === item.to;
        const Icon = item.icon;

        return (
          <Link
            key={item.to}
            href={item.to}
            title={collapsed ? item.label : undefined}
            className={cn(
              'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            <Icon className="w-5 h-5 shrink-0" />
            <span
              className={cn(
                'font-medium transition-opacity',
                collapsed && 'opacity-0 absolute'
              )}
            >
              {item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}

