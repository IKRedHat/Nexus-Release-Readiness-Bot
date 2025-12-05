/**
 * Skip Link Component
 * 
 * Accessibility feature that allows keyboard users to skip
 * directly to the main content area.
 */

'use client';

import { cn } from '@/lib/utils';

interface SkipLinkProps {
  href?: string;
  className?: string;
  children?: React.ReactNode;
}

export function SkipLink({
  href = '#main-content',
  className,
  children = 'Skip to main content',
}: SkipLinkProps) {
  return (
    <a
      href={href}
      className={cn(
        // Screen reader only by default
        'sr-only',
        // Visible on focus
        'focus:not-sr-only',
        'focus:fixed focus:top-4 focus:left-4 focus:z-[100]',
        'focus:px-4 focus:py-2',
        'focus:bg-primary focus:text-primary-foreground',
        'focus:rounded-md focus:shadow-lg',
        'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        'transition-all duration-200',
        className
      )}
    >
      {children}
    </a>
  );
}

/**
 * Main content wrapper that provides the skip link target
 */
interface MainContentProps {
  children: React.ReactNode;
  className?: string;
}

export function MainContent({ children, className }: MainContentProps) {
  return (
    <main
      id="main-content"
      tabIndex={-1}
      className={cn('outline-none', className)}
    >
      {children}
    </main>
  );
}

export default SkipLink;

