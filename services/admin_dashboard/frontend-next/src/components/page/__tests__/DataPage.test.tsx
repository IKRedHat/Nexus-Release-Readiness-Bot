/**
 * DataPage Component Tests
 * 
 * TDD: Tests written BEFORE implementation
 * 
 * DataPage is a wrapper component that handles:
 * - Loading states (shows PageLoadingState)
 * - Error states (shows PageErrorState)
 * - Page header
 * - Data rendering
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DataPage } from '../DataPage';

// Mock the Layout component
vi.mock('@/components/Layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="layout">{children}</div>,
}));

describe('DataPage', () => {
  describe('Loading State', () => {
    it('should show loading state when isLoading is true', () => {
      render(
        <DataPage
          title="Test Page"
          isLoading={true}
          error={null}
          data={null}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      // Should show skeletons
      const skeletons = document.querySelectorAll('[class*="skeleton"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should not show loading state when isLoading is false', () => {
      render(
        <DataPage
          title="Test Page"
          isLoading={false}
          error={null}
          data={{ test: 'data' }}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('should use custom loading layout', () => {
      render(
        <DataPage
          title="Test Page"
          isLoading={true}
          error={null}
          data={null}
          loadingLayout="grid"
          loadingCount={6}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      // Should render 6 skeletons in grid layout
      const container = document.querySelector('[data-testid="loading-items"]');
      const skeletons = container?.querySelectorAll('[class*="skeleton"]');
      expect(skeletons?.length).toBe(6);
    });
  });

  describe('Error State', () => {
    it('should show error state when error is present', () => {
      const mockError = new Error('Failed to fetch');
      
      render(
        <DataPage
          title="Test Page"
          isLoading={false}
          error={mockError}
          data={null}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.getByText(/unable to load/i)).toBeInTheDocument();
    });

    it('should show custom error message', () => {
      render(
        <DataPage
          title="Test Page"
          isLoading={false}
          error={new Error('Test error')}
          data={null}
          errorMessage="Custom error message"
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.getByText('Custom error message')).toBeInTheDocument();
    });

    it('should call onRetry when retry button is clicked', () => {
      const onRetry = vi.fn();
      
      render(
        <DataPage
          title="Test Page"
          isLoading={false}
          error={new Error('Error')}
          data={null}
          onRetry={onRetry}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      const retryButton = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryButton);
      
      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('Data Rendering', () => {
    it('should render children with data when available', () => {
      const mockData = { items: [1, 2, 3] };
      
      render(
        <DataPage
          title="Test Page"
          isLoading={false}
          error={null}
          data={mockData}
        >
          {(data) => (
            <div data-testid="content">
              {data.items.map(i => <span key={i}>{i}</span>)}
            </div>
          )}
        </DataPage>
      );
      
      expect(screen.getByTestId('content')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('should pass mutate function to children', () => {
      const mutate = vi.fn();
      const renderFn = vi.fn(() => <div>Content</div>);
      
      render(
        <DataPage
          title="Test Page"
          isLoading={false}
          error={null}
          data={{ test: 'data' }}
          mutate={mutate}
        >
          {renderFn}
        </DataPage>
      );
      
      expect(renderFn).toHaveBeenCalledWith(
        { test: 'data' },
        mutate
      );
    });
  });

  describe('Page Header', () => {
    it('should render page title', () => {
      render(
        <DataPage
          title="My Page Title"
          isLoading={false}
          error={null}
          data={{}}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('My Page Title');
    });

    it('should render page description', () => {
      render(
        <DataPage
          title="Title"
          description="Page description"
          isLoading={false}
          error={null}
          data={{}}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.getByText('Page description')).toBeInTheDocument();
    });

    it('should render actions', () => {
      render(
        <DataPage
          title="Title"
          isLoading={false}
          error={null}
          data={{}}
          actions={<button>Add New</button>}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.getByRole('button', { name: /add new/i })).toBeInTheDocument();
    });

    it('should not show header when showHeader is false', () => {
      render(
        <DataPage
          title="Title"
          isLoading={false}
          error={null}
          data={{}}
          showHeader={false}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.queryByRole('heading', { level: 1 })).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should show empty state when data is empty array', () => {
      render(
        <DataPage
          title="Title"
          isLoading={false}
          error={null}
          data={[]}
          emptyState={<div data-testid="empty">No items</div>}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.getByTestId('empty')).toBeInTheDocument();
    });

    it('should show empty state when data is null and not loading', () => {
      render(
        <DataPage
          title="Title"
          isLoading={false}
          error={null}
          data={null}
          emptyState={<div data-testid="empty">No data</div>}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.getByTestId('empty')).toBeInTheDocument();
    });

    it('should not show empty state when data exists', () => {
      render(
        <DataPage
          title="Title"
          isLoading={false}
          error={null}
          data={[1, 2, 3]}
          emptyState={<div data-testid="empty">No items</div>}
        >
          {() => <div data-testid="content">Content</div>}
        </DataPage>
      );
      
      expect(screen.queryByTestId('empty')).not.toBeInTheDocument();
      expect(screen.getByTestId('content')).toBeInTheDocument();
    });
  });

  describe('Layout', () => {
    it('should wrap content in Layout by default', () => {
      render(
        <DataPage
          title="Title"
          isLoading={false}
          error={null}
          data={{}}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.getByTestId('layout')).toBeInTheDocument();
    });

    it('should not wrap in Layout when useLayout is false', () => {
      render(
        <DataPage
          title="Title"
          isLoading={false}
          error={null}
          data={{}}
          useLayout={false}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.queryByTestId('layout')).not.toBeInTheDocument();
    });
  });

  describe('Breadcrumbs', () => {
    it('should pass breadcrumbs to header', () => {
      render(
        <DataPage
          title="Title"
          isLoading={false}
          error={null}
          data={{}}
          breadcrumbs={[
            { label: 'Home', href: '/' },
            { label: 'Current' },
          ]}
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Current')).toBeInTheDocument();
    });
  });

  describe('Custom Class', () => {
    it('should apply custom className', () => {
      render(
        <DataPage
          title="Title"
          isLoading={false}
          error={null}
          data={{}}
          className="custom-class"
        >
          {() => <div>Content</div>}
        </DataPage>
      );
      
      const container = document.querySelector('.custom-class');
      expect(container).toBeTruthy();
    });
  });

  describe('Hook Integration', () => {
    it('should work with SWR-like hook return value', () => {
      // Simulate SWR hook return
      const hookReturn = {
        data: { items: ['a', 'b', 'c'] },
        error: null,
        isLoading: false,
        mutate: vi.fn(),
      };
      
      render(
        <DataPage
          title="Title"
          {...hookReturn}
        >
          {(data) => (
            <ul>
              {data.items.map(item => <li key={item}>{item}</li>)}
            </ul>
          )}
        </DataPage>
      );
      
      expect(screen.getByText('a')).toBeInTheDocument();
      expect(screen.getByText('b')).toBeInTheDocument();
      expect(screen.getByText('c')).toBeInTheDocument();
    });
  });
});

