/**
 * PageHeader Component Tests
 * 
 * TDD: Tests written BEFORE implementation
 * 
 * This component provides a consistent header for all pages
 * with title, description, and action buttons.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PageHeader } from '../PageHeader';

describe('PageHeader', () => {
  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(<PageHeader title="Dashboard" />);
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    it('should render the title', () => {
      render(<PageHeader title="Releases" />);
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Releases');
    });

    it('should render the description when provided', () => {
      render(<PageHeader title="Title" description="This is a description" />);
      expect(screen.getByText('This is a description')).toBeInTheDocument();
    });

    it('should not render description element when not provided', () => {
      render(<PageHeader title="Title" />);
      const descElement = document.querySelector('[data-testid="page-description"]');
      expect(descElement).toBeNull();
    });
  });

  describe('Action Buttons', () => {
    it('should render actions when provided', () => {
      render(
        <PageHeader 
          title="Title" 
          actions={<button>New Item</button>} 
        />
      );
      expect(screen.getByRole('button', { name: /new item/i })).toBeInTheDocument();
    });

    it('should render multiple actions', () => {
      render(
        <PageHeader 
          title="Title" 
          actions={
            <>
              <button>Action 1</button>
              <button>Action 2</button>
            </>
          } 
        />
      );
      expect(screen.getByRole('button', { name: /action 1/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /action 2/i })).toBeInTheDocument();
    });

    it('should not render actions container when actions not provided', () => {
      render(<PageHeader title="Title" />);
      const actionsContainer = document.querySelector('[data-testid="page-actions"]');
      expect(actionsContainer).toBeNull();
    });
  });

  describe('Breadcrumbs', () => {
    it('should render breadcrumbs when provided', () => {
      render(
        <PageHeader 
          title="Title" 
          breadcrumbs={[
            { label: 'Home', href: '/' },
            { label: 'Settings', href: '/settings' },
          ]}
        />
      );
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('should render breadcrumb links correctly', () => {
      render(
        <PageHeader 
          title="Title" 
          breadcrumbs={[
            { label: 'Home', href: '/' },
            { label: 'Current' },
          ]}
        />
      );
      
      const homeLink = screen.getByText('Home').closest('a');
      expect(homeLink).toHaveAttribute('href', '/');
      
      // Current page should not be a link
      const currentItem = screen.getByText('Current');
      expect(currentItem.closest('a')).toBeNull();
    });

    it('should not render breadcrumbs when not provided', () => {
      render(<PageHeader title="Title" />);
      const breadcrumbs = document.querySelector('[data-testid="breadcrumbs"]');
      expect(breadcrumbs).toBeNull();
    });
  });

  describe('Badge', () => {
    it('should render badge when provided', () => {
      render(<PageHeader title="Title" badge="Beta" />);
      expect(screen.getByText('Beta')).toBeInTheDocument();
    });

    it('should render badge with custom variant', () => {
      render(<PageHeader title="Title" badge="New" badgeVariant="secondary" />);
      const badge = screen.getByText('New');
      expect(badge).toBeInTheDocument();
    });

    it('should not render badge when not provided', () => {
      render(<PageHeader title="Title" />);
      const badge = document.querySelector('[data-testid="page-badge"]');
      expect(badge).toBeNull();
    });
  });

  describe('Subtitle', () => {
    it('should render subtitle when provided', () => {
      render(<PageHeader title="Title" subtitle="Last updated: Today" />);
      expect(screen.getByText('Last updated: Today')).toBeInTheDocument();
    });

    it('should not render subtitle when not provided', () => {
      render(<PageHeader title="Title" />);
      const subtitle = document.querySelector('[data-testid="page-subtitle"]');
      expect(subtitle).toBeNull();
    });
  });

  describe('Icon', () => {
    it('should render icon when provided', () => {
      const Icon = () => <svg data-testid="custom-icon" />;
      render(<PageHeader title="Title" icon={<Icon />} />);
      expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    });

    it('should not render icon container when not provided', () => {
      render(<PageHeader title="Title" />);
      const iconContainer = document.querySelector('[data-testid="page-icon"]');
      expect(iconContainer).toBeNull();
    });
  });

  describe('Layout', () => {
    it('should have flex layout by default', () => {
      render(<PageHeader title="Title" />);
      const container = document.querySelector('[data-testid="page-header"]');
      expect(container?.className).toContain('flex');
    });

    it('should align items between title and actions', () => {
      render(<PageHeader title="Title" actions={<button>Action</button>} />);
      const container = document.querySelector('[data-testid="page-header"]');
      expect(container?.className).toContain('justify-between');
    });

    it('should stack on mobile (responsive)', () => {
      render(<PageHeader title="Title" actions={<button>Action</button>} />);
      const container = document.querySelector('[data-testid="page-header"]');
      // Should have flex-col for mobile, then flex-row for larger screens
      expect(container?.className).toMatch(/flex-col|sm:flex-row|md:flex-row/);
    });
  });

  describe('Back Button', () => {
    it('should render back button when showBackButton is true', () => {
      render(<PageHeader title="Title" showBackButton />);
      const backButton = screen.getByRole('button', { name: /back/i });
      expect(backButton).toBeInTheDocument();
    });

    it('should call onBack when back button is clicked', () => {
      const onBack = vi.fn();
      render(<PageHeader title="Title" showBackButton onBack={onBack} />);
      
      const backButton = screen.getByRole('button', { name: /back/i });
      fireEvent.click(backButton);
      
      expect(onBack).toHaveBeenCalledTimes(1);
    });

    it('should not render back button by default', () => {
      render(<PageHeader title="Title" />);
      const backButton = screen.queryByRole('button', { name: /back/i });
      expect(backButton).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<PageHeader title="Page Title" />);
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Page Title');
    });

    it('should have accessible description', () => {
      render(<PageHeader title="Title" description="Description text" />);
      expect(screen.getByText('Description text')).toBeInTheDocument();
    });

    it('should have accessible breadcrumb navigation', () => {
      render(
        <PageHeader 
          title="Title" 
          breadcrumbs={[
            { label: 'Home', href: '/' },
            { label: 'Settings' },
          ]}
        />
      );
      
      const nav = document.querySelector('nav[aria-label="Breadcrumb"]');
      expect(nav).toBeTruthy();
    });
  });

  describe('Custom Styling', () => {
    it('should apply custom className', () => {
      render(<PageHeader title="Title" className="custom-class" />);
      const container = document.querySelector('.custom-class');
      expect(container).toBeTruthy();
    });

    it('should merge custom className with defaults', () => {
      render(<PageHeader title="Title" className="my-custom" />);
      const container = document.querySelector('.my-custom');
      expect(container?.className).toContain('flex');
    });

    it('should support custom title className', () => {
      render(<PageHeader title="Title" titleClassName="text-red-500" />);
      const title = screen.getByRole('heading');
      expect(title.className).toContain('text-red-500');
    });
  });

  describe('Loading State', () => {
    it('should show loading state when isLoading is true', () => {
      render(<PageHeader title="Title" isLoading />);
      // Should show skeleton instead of title
      const skeleton = document.querySelector('[class*="skeleton"]');
      expect(skeleton).toBeTruthy();
    });

    it('should not show loading state by default', () => {
      render(<PageHeader title="Title" />);
      expect(screen.getByText('Title')).toBeInTheDocument();
    });
  });

  describe('Divider', () => {
    it('should render divider when showDivider is true', () => {
      render(<PageHeader title="Title" showDivider />);
      const divider = document.querySelector('[data-testid="page-divider"]');
      expect(divider).toBeTruthy();
    });

    it('should not render divider by default', () => {
      render(<PageHeader title="Title" />);
      const divider = document.querySelector('[data-testid="page-divider"]');
      expect(divider).toBeNull();
    });
  });

  describe('Size Variants', () => {
    it('should apply default (large) size', () => {
      render(<PageHeader title="Title" />);
      const title = screen.getByRole('heading');
      expect(title.className).toContain('text-4xl');
    });

    it('should apply small size', () => {
      render(<PageHeader title="Title" size="sm" />);
      const title = screen.getByRole('heading');
      expect(title.className).toContain('text-2xl');
    });

    it('should apply medium size', () => {
      render(<PageHeader title="Title" size="md" />);
      const title = screen.getByRole('heading');
      expect(title.className).toContain('text-3xl');
    });

    it('should apply large size', () => {
      render(<PageHeader title="Title" size="lg" />);
      const title = screen.getByRole('heading');
      expect(title.className).toContain('text-4xl');
    });
  });
});

