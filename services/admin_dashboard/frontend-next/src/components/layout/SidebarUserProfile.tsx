'use client';

import { LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { User } from '@/types';

/**
 * Props for SidebarUserProfile component
 */
export interface SidebarUserProfileProps {
  /** Current user (can be null if not logged in) */
  user: User | null;
  /** Callback when logout is clicked */
  onLogout: () => void;
  /** Whether the sidebar is collapsed */
  collapsed?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * SidebarUserProfile Component
 * 
 * Displays user profile and logout button at the bottom of the sidebar.
 * 
 * @example
 * <SidebarUserProfile 
 *   user={user} 
 *   onLogout={handleLogout} 
 *   collapsed={isCollapsed} 
 * />
 */
export function SidebarUserProfile({
  user,
  onLogout,
  collapsed = false,
  className,
}: SidebarUserProfileProps) {
  // Get user initial for avatar
  const getInitial = () => {
    if (!user) return '?';
    if (user.name) return user.name.charAt(0).toUpperCase();
    if (user.email) return user.email.charAt(0).toLowerCase();
    return '?';
  };

  return (
    <div
      className={cn(
        'absolute bottom-0 left-0 right-0 p-4 border-t border-border bg-card',
        className
      )}
    >
      {collapsed ? (
        // Collapsed view: just avatar and logout
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
            <span className="text-sm font-bold text-primary">
              {getInitial()}
            </span>
          </div>
          <button
            onClick={onLogout}
            className="p-2 hover:bg-accent rounded-lg text-muted-foreground hover:text-foreground"
            aria-label="Logout"
            title="Logout"
          >
            <LogOut size={18} />
          </button>
        </div>
      ) : (
        // Expanded view: full profile
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 min-w-0">
            {/* Avatar */}
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <span className="text-sm font-bold text-primary">
                {getInitial()}
              </span>
            </div>
            
            {/* User info */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                {user?.name || 'User'}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.email}
              </p>
            </div>
          </div>

          {/* Logout button */}
          <button
            onClick={onLogout}
            className="p-2 hover:bg-accent rounded-lg text-muted-foreground hover:text-foreground shrink-0"
            aria-label="Logout"
            title="Logout"
          >
            <LogOut size={18} />
          </button>
        </div>
      )}
    </div>
  );
}

