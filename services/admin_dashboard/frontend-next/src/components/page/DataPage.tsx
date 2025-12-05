'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import Layout from '@/components/Layout';
import { PageHeader, PageHeaderProps } from './PageHeader';
import { PageLoadingState, PageLoadingStateProps } from './PageLoadingState';
import { PageErrorState, PageErrorStateProps } from './PageErrorState';

/**
 * Breadcrumb item for navigation
 */
export interface BreadcrumbItem {
  /** Display label */
  label: string;
  /** Link href (optional for current page) */
  href?: string;
}

/**
 * Props for DataPage component
 */
export interface DataPageProps<T> {
  /** Page title */
  title: string;
  /** Page description (optional) */
  description?: string;
  /** Whether data is loading */
  isLoading: boolean;
  /** Error object if fetch failed */
  error: Error | null;
  /** Fetched data */
  data: T | null;
  /** Render function for data - receives data and optional mutate function */
  children: (data: T, mutate?: () => void) => ReactNode;
  /** SWR mutate function */
  mutate?: () => void;
  /** Callback when retry is clicked */
  onRetry?: () => void;
  /** Custom error message */
  errorMessage?: string;
  /** Action buttons for header */
  actions?: ReactNode;
  /** Breadcrumb navigation */
  breadcrumbs?: BreadcrumbItem[];
  /** Whether to show header */
  showHeader?: boolean;
  /** Whether to use Layout wrapper */
  useLayout?: boolean;
  /** Empty state component when data is empty */
  emptyState?: ReactNode;
  /** Loading layout: list or grid */
  loadingLayout?: 'list' | 'grid';
  /** Number of loading skeletons */
  loadingCount?: number;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Check if data is considered empty
 */
function isDataEmpty<T>(data: T | null): boolean {
  if (data === null || data === undefined) return true;
  if (Array.isArray(data) && data.length === 0) return true;
  return false;
}

/**
 * DataPage Component
 * 
 * A higher-order component that handles common page patterns:
 * - Loading states with skeletons
 * - Error states with retry
 * - Page header with title and actions
 * - Empty states
 * - Layout wrapping
 * 
 * Designed to work seamlessly with SWR/React Query hooks.
 * 
 * @example
 * // Basic usage
 * <DataPage
 *   title="Users"
 *   description="Manage system users"
 *   isLoading={isLoading}
 *   error={error}
 *   data={users}
 *   onRetry={mutate}
 *   actions={<Button>Add User</Button>}
 * >
 *   {(users) => (
 *     <UserTable users={users} />
 *   )}
 * </DataPage>
 * 
 * @example
 * // With SWR hook
 * const { data, error, isLoading, mutate } = useUsers();
 * 
 * <DataPage
 *   title="Users"
 *   isLoading={isLoading}
 *   error={error}
 *   data={data}
 *   mutate={mutate}
 *   onRetry={mutate}
 *   emptyState={<EmptyUsers />}
 * >
 *   {(users, mutate) => (
 *     <UserList users={users} onDelete={() => mutate?.()} />
 *   )}
 * </DataPage>
 */
export function DataPage<T>({
  title,
  description,
  isLoading,
  error,
  data,
  children,
  mutate,
  onRetry,
  errorMessage,
  actions,
  breadcrumbs,
  showHeader = true,
  useLayout = true,
  emptyState,
  loadingLayout = 'list',
  loadingCount = 3,
  className,
}: DataPageProps<T>) {
  // Determine what to render based on state
  const renderContent = () => {
    // 1. Loading state
    if (isLoading) {
      return (
        <PageLoadingState
          layout={loadingLayout}
          count={loadingCount}
        />
      );
    }

    // 2. Error state
    if (error) {
      return (
        <PageErrorState
          title="Unable to Load Data"
          message={errorMessage || error.message || 'An unexpected error occurred'}
          onRetry={onRetry}
        />
      );
    }

    // 3. Empty state
    if (isDataEmpty(data) && emptyState) {
      return emptyState;
    }

    // 4. Empty without custom empty state - show error-like state
    if (isDataEmpty(data)) {
      return (
        <PageErrorState
          title="No Data Available"
          message="There is no data to display at this time."
          variant="empty"
        />
      );
    }

    // 5. Normal render with data
    return children(data as T, mutate);
  };

  // Page content
  const pageContent = (
    <div className={cn('p-6', className)}>
      {/* Header */}
      {showHeader && (
        <PageHeader
          title={title}
          description={description}
          actions={actions}
          breadcrumbs={breadcrumbs}
          className="mb-6"
        />
      )}

      {/* Content */}
      {renderContent()}
    </div>
  );

  // Wrap in Layout if needed
  if (useLayout) {
    return <Layout>{pageContent}</Layout>;
  }

  return pageContent;
}

export default DataPage;

