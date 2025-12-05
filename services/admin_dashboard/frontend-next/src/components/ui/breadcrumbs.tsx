/**
 * Breadcrumbs Component
 * 
 * Displays navigation breadcrumb trail based on current route.
 */

'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

// Route label mappings
const routeLabels: Record<string, string> = {
  '': 'Dashboard',
  releases: 'Releases',
  health: 'Health Monitor',
  metrics: 'Metrics',
  settings: 'Settings',
  'feature-requests': 'Feature Requests',
  admin: 'Administration',
  users: 'Users',
  roles: 'Roles',
  debug: 'Debug',
  login: 'Login',
};

interface BreadcrumbItem {
  label: string;
  href: string;
  isCurrentPage: boolean;
}

interface BreadcrumbsProps {
  className?: string;
  showHome?: boolean;
  separator?: React.ReactNode;
}

export function Breadcrumbs({
  className,
  showHome = true,
  separator,
}: BreadcrumbsProps) {
  const pathname = usePathname();

  // Don't show breadcrumbs on login page
  if (pathname === '/login') {
    return null;
  }

  // Parse pathname into breadcrumb items
  const segments = pathname.split('/').filter(Boolean);
  
  const breadcrumbs: BreadcrumbItem[] = segments.map((segment, index) => {
    const href = '/' + segments.slice(0, index + 1).join('/');
    const label = routeLabels[segment] || formatSegmentLabel(segment);
    const isCurrentPage = index === segments.length - 1;

    return {
      label,
      href,
      isCurrentPage,
    };
  });

  // Add home at the beginning if requested
  if (showHome) {
    breadcrumbs.unshift({
      label: 'Home',
      href: '/',
      isCurrentPage: pathname === '/',
    });
  }

  // Don't render if only home
  if (breadcrumbs.length <= 1) {
    return null;
  }

  const Separator = separator || (
    <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
  );

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center text-sm', className)}
    >
      <ol className="flex items-center gap-1.5">
        {breadcrumbs.map((breadcrumb, index) => (
          <li key={breadcrumb.href} className="flex items-center gap-1.5">
            {index > 0 && Separator}
            
            {breadcrumb.isCurrentPage ? (
              <span
                className="font-medium text-foreground"
                aria-current="page"
              >
                {index === 0 && showHome ? (
                  <Home className="h-4 w-4" />
                ) : (
                  breadcrumb.label
                )}
              </span>
            ) : (
              <Link
                href={breadcrumb.href}
                className={cn(
                  'text-muted-foreground hover:text-foreground transition-colors',
                  'hover:underline underline-offset-4'
                )}
              >
                {index === 0 && showHome ? (
                  <Home className="h-4 w-4" />
                ) : (
                  breadcrumb.label
                )}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

/**
 * Format a URL segment into a readable label
 */
function formatSegmentLabel(segment: string): string {
  // Handle UUIDs or IDs
  if (isUUID(segment) || /^\d+$/.test(segment)) {
    return `#${segment.slice(0, 8)}...`;
  }

  // Convert kebab-case or snake_case to Title Case
  return segment
    .replace(/[-_]/g, ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Check if a string is a UUID
 */
function isUUID(str: string): boolean {
  const uuidRegex =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(str);
}

/**
 * Hook to get current breadcrumbs
 */
export function useBreadcrumbs(): BreadcrumbItem[] {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);

  return segments.map((segment, index) => {
    const href = '/' + segments.slice(0, index + 1).join('/');
    const label = routeLabels[segment] || formatSegmentLabel(segment);
    const isCurrentPage = index === segments.length - 1;

    return {
      label,
      href,
      isCurrentPage,
    };
  });
}

export default Breadcrumbs;

