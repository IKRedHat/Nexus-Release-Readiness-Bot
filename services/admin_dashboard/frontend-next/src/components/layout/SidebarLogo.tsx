'use client';

import Link from 'next/link';
import { Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Props for SidebarLogo component
 */
export interface SidebarLogoProps {
  /** Whether the sidebar is collapsed */
  collapsed?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * SidebarLogo Component
 * 
 * Displays the Nexus logo and branding in the sidebar.
 * Shows only icon when collapsed.
 * 
 * @example
 * <SidebarLogo collapsed={isCollapsed} />
 */
export function SidebarLogo({ collapsed = false, className }: SidebarLogoProps) {
  return (
    <div
      data-testid="sidebar-logo"
      className={cn(
        'h-16 flex items-center border-b border-border',
        collapsed ? 'justify-center px-2' : 'px-4',
        className
      )}
    >
      <Link href="/" className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-emerald-600 flex items-center justify-center shrink-0">
          <Zap className="w-6 h-6 text-background" />
        </div>
        
        {!collapsed && (
          <div className="flex flex-col">
            <h1 className="text-lg font-bold text-foreground">Nexus</h1>
            <p className="text-xs text-muted-foreground">Admin Dashboard</p>
          </div>
        )}
      </Link>
    </div>
  );
}

