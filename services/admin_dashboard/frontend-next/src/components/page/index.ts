/**
 * Page Components
 * 
 * Reusable components for building consistent page layouts.
 * These components reduce code duplication across pages.
 */

export { PageLoadingState } from './PageLoadingState';
export type { PageLoadingStateProps, LoadingLayout } from './PageLoadingState';

export { PageErrorState } from './PageErrorState';
export type { PageErrorStateProps, ErrorVariant } from './PageErrorState';

export { PageHeader } from './PageHeader';
export type { PageHeaderProps, BreadcrumbItem as PageBreadcrumbItem, HeaderSize, BadgeVariant } from './PageHeader';

export { DataPage } from './DataPage';
export type { DataPageProps, BreadcrumbItem } from './DataPage';

