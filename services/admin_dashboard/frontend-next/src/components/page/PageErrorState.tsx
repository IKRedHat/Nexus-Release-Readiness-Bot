'use client';

import { ReactNode, useState } from 'react';
import { AlertCircle, AlertTriangle, Info, FileQuestion, Inbox, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

/**
 * Error state variants
 */
export type ErrorVariant = 'error' | 'warning' | 'info' | 'not-found' | 'empty';

/**
 * Props for PageErrorState component
 */
export interface PageErrorStateProps {
  /** Error title/heading */
  title: string;
  /** Error message/description */
  message: string;
  /** Error variant for styling */
  variant?: ErrorVariant;
  /** Callback when retry button is clicked */
  onRetry?: () => void;
  /** Custom text for retry button */
  retryText?: string;
  /** Callback for secondary action */
  onSecondaryAction?: () => void;
  /** Text for secondary action button */
  secondaryActionText?: string;
  /** Custom icon element */
  icon?: ReactNode;
  /** Whether to show the icon */
  showIcon?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Full width layout (no max-width) */
  fullWidth?: boolean;
  /** Compact layout with less padding */
  compact?: boolean;
  /** Detailed error information (for debugging) */
  errorDetails?: string;
  /** Show toggle for error details */
  showDetailsToggle?: boolean;
}

/**
 * Variant configurations
 */
const variantConfig: Record<ErrorVariant, { 
  icon: typeof AlertCircle; 
  iconClass: string;
  containerClass: string;
}> = {
  error: {
    icon: AlertCircle,
    iconClass: 'text-destructive',
    containerClass: 'error',
  },
  warning: {
    icon: AlertTriangle,
    iconClass: 'text-yellow-500',
    containerClass: 'warning',
  },
  info: {
    icon: Info,
    iconClass: 'text-blue-500',
    containerClass: 'info',
  },
  'not-found': {
    icon: FileQuestion,
    iconClass: 'text-muted-foreground',
    containerClass: 'not-found',
  },
  empty: {
    icon: Inbox,
    iconClass: 'text-muted-foreground',
    containerClass: 'empty',
  },
};

/**
 * PageErrorState Component
 * 
 * Displays an error state with optional retry functionality.
 * Supports multiple variants, custom icons, and detailed error info.
 * 
 * @example
 * // Basic usage
 * <PageErrorState 
 *   title="Unable to Load Data" 
 *   message="Could not fetch data from the server."
 *   onRetry={() => refetch()}
 * />
 * 
 * @example
 * // With variant and secondary action
 * <PageErrorState 
 *   title="Page Not Found" 
 *   message="The page you're looking for doesn't exist."
 *   variant="not-found"
 *   onSecondaryAction={() => router.push('/')}
 *   secondaryActionText="Go Home"
 * />
 */
export function PageErrorState({
  title,
  message,
  variant = 'error',
  onRetry,
  retryText = 'Retry',
  onSecondaryAction,
  secondaryActionText,
  icon,
  showIcon = true,
  className,
  fullWidth = false,
  compact = false,
  errorDetails,
  showDetailsToggle = false,
}: PageErrorStateProps) {
  const [showDetails, setShowDetails] = useState(!showDetailsToggle);
  const config = variantConfig[variant];
  const IconComponent = config.icon;

  return (
    <Card
      role="alert"
      aria-live="polite"
      data-testid="error-state"
      className={cn(
        'mx-auto',
        !fullWidth && 'max-w-2xl',
        compact ? 'p-4' : 'mt-20',
        config.containerClass,
        className
      )}
    >
      <CardContent className={cn('pt-6', compact && 'py-4')}>
        <div className="text-center">
          {/* Icon */}
          {showIcon && (
            <div data-testid="error-icon" className="mb-4">
              {icon || (
                <IconComponent 
                  className={cn('w-16 h-16 mx-auto', config.iconClass)} 
                />
              )}
            </div>
          )}

          {/* Title */}
          <h2 className="text-2xl font-bold text-foreground mb-2">
            {title}
          </h2>

          {/* Message */}
          {message && (
            <p className="text-muted-foreground mb-6">
              {message}
            </p>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            {onRetry && (
              <Button onClick={onRetry}>
                {retryText}
              </Button>
            )}
            {onSecondaryAction && secondaryActionText && (
              <Button variant="outline" onClick={onSecondaryAction}>
                {secondaryActionText}
              </Button>
            )}
          </div>

          {/* Error Details */}
          {errorDetails && (
            <div className="mt-6">
              {showDetailsToggle ? (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowDetails(!showDetails)}
                    className="text-muted-foreground"
                  >
                    {showDetails ? (
                      <>
                        <ChevronUp className="w-4 h-4 mr-1" />
                        Hide Details
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-4 h-4 mr-1" />
                        Show Details
                      </>
                    )}
                  </Button>
                  {showDetails && (
                    <pre className="mt-4 p-4 bg-muted rounded-lg text-xs text-left overflow-auto max-h-48">
                      {errorDetails}
                    </pre>
                  )}
                </>
              ) : (
                <pre className="p-4 bg-muted rounded-lg text-xs text-left overflow-auto max-h-48">
                  {errorDetails}
                </pre>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Export types for external use
 */
export type { ErrorVariant };

