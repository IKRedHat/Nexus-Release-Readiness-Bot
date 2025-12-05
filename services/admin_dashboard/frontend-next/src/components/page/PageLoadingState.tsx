'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

/**
 * Layout types for the loading state
 * - cards: Grid layout with responsive columns (default)
 * - list: Vertical list layout
 * - grid: Standard grid layout
 */
export type LoadingLayout = 'cards' | 'list' | 'grid';

/**
 * Props for PageLoadingState component
 */
export interface PageLoadingStateProps {
  /** Layout variant for skeleton items */
  layout?: LoadingLayout;
  /** Number of skeleton items to display */
  count?: number;
  /** Whether to show the title skeleton */
  showTitle?: boolean;
  /** Whether to show the description skeleton */
  showDescription?: boolean;
  /** Custom class name for the container */
  className?: string;
  /** Custom height for skeleton items (Tailwind class) */
  itemHeight?: string;
  /** Custom aria-label for accessibility */
  ariaLabel?: string;
}

/**
 * Layout class configurations
 */
const layoutClasses: Record<LoadingLayout, string> = {
  cards: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6',
  list: 'flex flex-col gap-4',
  grid: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6',
};

/**
 * Default heights for different layouts
 */
const defaultHeights: Record<LoadingLayout, string> = {
  cards: 'h-32',
  list: 'h-20',
  grid: 'h-48',
};

/**
 * PageLoadingState Component
 * 
 * Displays a loading skeleton while page data is being fetched.
 * Supports different layout variants and is fully accessible.
 * 
 * @example
 * // Basic usage
 * <PageLoadingState />
 * 
 * @example
 * // With custom layout and count
 * <PageLoadingState layout="grid" count={6} />
 * 
 * @example
 * // Without title/description
 * <PageLoadingState showTitle={false} showDescription={false} />
 */
export function PageLoadingState({
  layout = 'cards',
  count = 4,
  showTitle = true,
  showDescription = true,
  className,
  itemHeight,
  ariaLabel = 'Loading content...',
}: PageLoadingStateProps) {
  const height = itemHeight || defaultHeights[layout];

  return (
    <div
      role="status"
      aria-busy="true"
      aria-label={ariaLabel}
      className={cn('space-y-8', className)}
    >
      {/* Title and Description Skeletons */}
      {(showTitle || showDescription) && (
        <div className="space-y-2">
          {showTitle && (
            <Skeleton
              data-testid="loading-title"
              className="h-10 w-64"
            />
          )}
          {showDescription && (
            <Skeleton
              data-testid="loading-description"
              className="h-6 w-96"
            />
          )}
        </div>
      )}

      {/* Skeleton Items */}
      <div
        data-testid="loading-items"
        className={layoutClasses[layout]}
      >
        {Array.from({ length: count }).map((_, index) => (
          <Skeleton
            key={index}
            className={cn(height, 'rounded-lg')}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Export type for external use
 */
export type { PageLoadingStateProps as PageLoadingStatePropsType };

