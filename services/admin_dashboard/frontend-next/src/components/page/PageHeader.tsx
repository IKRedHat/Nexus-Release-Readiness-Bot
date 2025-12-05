'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { ArrowLeft, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

/**
 * Size variants for the header
 */
export type HeaderSize = 'sm' | 'md' | 'lg';

/**
 * Badge variant type
 */
export type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

/**
 * Breadcrumb item
 */
export interface BreadcrumbItem {
  label: string;
  href?: string;
}

/**
 * Props for PageHeader component
 */
export interface PageHeaderProps {
  /** Page title */
  title: string;
  /** Page description */
  description?: string;
  /** Action buttons or elements to display */
  actions?: ReactNode;
  /** Breadcrumb navigation */
  breadcrumbs?: BreadcrumbItem[];
  /** Badge text to display next to title */
  badge?: string;
  /** Badge variant */
  badgeVariant?: BadgeVariant;
  /** Subtitle text (e.g., "Last updated: Today") */
  subtitle?: string;
  /** Icon to display before title */
  icon?: ReactNode;
  /** Whether to show back button */
  showBackButton?: boolean;
  /** Callback when back button is clicked */
  onBack?: () => void;
  /** Custom class name for container */
  className?: string;
  /** Custom class name for title */
  titleClassName?: string;
  /** Whether the header is in loading state */
  isLoading?: boolean;
  /** Whether to show a divider below the header */
  showDivider?: boolean;
  /** Size variant */
  size?: HeaderSize;
}

/**
 * Size configurations
 */
const sizeConfig: Record<HeaderSize, { title: string; description: string }> = {
  sm: { title: 'text-2xl', description: 'text-sm' },
  md: { title: 'text-3xl', description: 'text-base' },
  lg: { title: 'text-4xl', description: 'text-lg' },
};

/**
 * PageHeader Component
 * 
 * Provides a consistent header layout for all pages with support for:
 * - Title, description, and subtitle
 * - Action buttons
 * - Breadcrumb navigation
 * - Badges
 * - Back button
 * - Loading state
 * 
 * @example
 * // Basic usage
 * <PageHeader title="Dashboard" description="Welcome to your dashboard" />
 * 
 * @example
 * // With actions
 * <PageHeader 
 *   title="Releases" 
 *   description="Manage releases"
 *   actions={<Button><Plus /> New Release</Button>}
 * />
 * 
 * @example
 * // With breadcrumbs
 * <PageHeader 
 *   title="Edit User"
 *   breadcrumbs={[
 *     { label: 'Users', href: '/admin/users' },
 *     { label: 'Edit' },
 *   ]}
 * />
 */
export function PageHeader({
  title,
  description,
  actions,
  breadcrumbs,
  badge,
  badgeVariant = 'default',
  subtitle,
  icon,
  showBackButton = false,
  onBack,
  className,
  titleClassName,
  isLoading = false,
  showDivider = false,
  size = 'lg',
}: PageHeaderProps) {
  const sizeStyles = sizeConfig[size];

  // Handle back button click
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else if (typeof window !== 'undefined') {
      window.history.back();
    }
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav aria-label="Breadcrumb" data-testid="breadcrumbs">
          <ol className="flex items-center gap-2 text-sm text-muted-foreground">
            {breadcrumbs.map((crumb, index) => (
              <li key={index} className="flex items-center gap-2">
                {crumb.href ? (
                  <Link 
                    href={crumb.href}
                    className="hover:text-foreground transition-colors"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-foreground font-medium">{crumb.label}</span>
                )}
                {index < breadcrumbs.length - 1 && (
                  <ChevronRight className="w-4 h-4" />
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}

      {/* Main Header */}
      <div 
        data-testid="page-header"
        className={cn(
          'flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'
        )}
      >
        {/* Left Side: Back button, Icon, Title, Badge, Description */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            {/* Back Button */}
            {showBackButton && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleBack}
                aria-label="Go back"
                className="shrink-0"
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>
            )}

            {/* Icon */}
            {icon && (
              <div data-testid="page-icon" className="shrink-0">
                {icon}
              </div>
            )}

            {/* Title and Badge */}
            <div className="flex items-center gap-3 flex-wrap">
              {isLoading ? (
                <Skeleton className="h-10 w-64" />
              ) : (
                <h1 
                  className={cn(
                    'font-bold text-foreground',
                    sizeStyles.title,
                    titleClassName
                  )}
                >
                  {title}
                </h1>
              )}
              
              {badge && !isLoading && (
                <Badge 
                  data-testid="page-badge"
                  variant={badgeVariant as any}
                >
                  {badge}
                </Badge>
              )}
            </div>
          </div>

          {/* Subtitle */}
          {subtitle && !isLoading && (
            <p 
              data-testid="page-subtitle"
              className="text-sm text-muted-foreground mt-1"
            >
              {subtitle}
            </p>
          )}

          {/* Description */}
          {description && !isLoading && (
            <p 
              data-testid="page-description"
              className={cn(
                'text-muted-foreground mt-2',
                sizeStyles.description
              )}
            >
              {description}
            </p>
          )}

          {isLoading && (description || subtitle) && (
            <Skeleton className="h-6 w-96 mt-2" />
          )}
        </div>

        {/* Right Side: Actions */}
        {actions && !isLoading && (
          <div 
            data-testid="page-actions"
            className="flex items-center gap-2 shrink-0"
          >
            {actions}
          </div>
        )}

        {isLoading && actions && (
          <Skeleton className="h-10 w-32" />
        )}
      </div>

      {/* Divider */}
      {showDivider && (
        <div 
          data-testid="page-divider"
          className="border-b border-border"
        />
      )}
    </div>
  );
}

/**
 * Export types for external use
 */
export type { BreadcrumbItem, HeaderSize, BadgeVariant };

