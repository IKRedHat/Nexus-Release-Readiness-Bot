/**
 * PageLoadingState Component Tests
 * 
 * TDD: Tests written BEFORE implementation
 * 
 * This component displays a loading skeleton while data is being fetched.
 * It supports different layouts: cards, list, and grid.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PageLoadingState } from '../PageLoadingState';

describe('PageLoadingState', () => {
  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(<PageLoadingState />);
      // Should render skeletons
      expect(document.querySelector('[class*="skeleton"]')).toBeTruthy();
    });

    it('should render title skeleton by default', () => {
      render(<PageLoadingState />);
      // First skeleton should be for title
      const skeletons = document.querySelectorAll('[class*="skeleton"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should render correct number of skeleton items with default count', () => {
      render(<PageLoadingState />);
      // Default count should be 4
      const container = document.querySelector('[data-testid="loading-items"]');
      expect(container).toBeTruthy();
      const items = container?.querySelectorAll('[class*="skeleton"]');
      expect(items?.length).toBe(4);
    });

    it('should render custom number of skeleton items', () => {
      render(<PageLoadingState count={6} />);
      const container = document.querySelector('[data-testid="loading-items"]');
      const items = container?.querySelectorAll('[class*="skeleton"]');
      expect(items?.length).toBe(6);
    });

    it('should render with count of 1', () => {
      render(<PageLoadingState count={1} />);
      const container = document.querySelector('[data-testid="loading-items"]');
      const items = container?.querySelectorAll('[class*="skeleton"]');
      expect(items?.length).toBe(1);
    });
  });

  describe('Layout Variants', () => {
    it('should apply cards layout by default', () => {
      render(<PageLoadingState />);
      const container = document.querySelector('[data-testid="loading-items"]');
      expect(container?.className).toContain('grid');
    });

    it('should apply cards layout when specified', () => {
      render(<PageLoadingState layout="cards" />);
      const container = document.querySelector('[data-testid="loading-items"]');
      expect(container?.className).toContain('grid');
      expect(container?.className).toContain('grid-cols');
    });

    it('should apply list layout when specified', () => {
      render(<PageLoadingState layout="list" />);
      const container = document.querySelector('[data-testid="loading-items"]');
      expect(container?.className).toContain('flex');
      expect(container?.className).toContain('flex-col');
    });

    it('should apply grid layout when specified', () => {
      render(<PageLoadingState layout="grid" />);
      const container = document.querySelector('[data-testid="loading-items"]');
      expect(container?.className).toContain('grid');
    });
  });

  describe('Accessibility', () => {
    it('should have role="status" for screen readers', () => {
      render(<PageLoadingState />);
      const container = document.querySelector('[role="status"]');
      expect(container).toBeTruthy();
    });

    it('should have aria-busy="true"', () => {
      render(<PageLoadingState />);
      const container = document.querySelector('[aria-busy="true"]');
      expect(container).toBeTruthy();
    });

    it('should have aria-label describing loading state', () => {
      render(<PageLoadingState />);
      const container = document.querySelector('[aria-label]');
      expect(container).toBeTruthy();
      expect(container?.getAttribute('aria-label')).toContain('Loading');
    });

    it('should support custom aria-label', () => {
      render(<PageLoadingState ariaLabel="Loading releases data" />);
      const container = document.querySelector('[aria-label="Loading releases data"]');
      expect(container).toBeTruthy();
    });
  });

  describe('Title Section', () => {
    it('should show title skeleton by default', () => {
      render(<PageLoadingState />);
      const titleSection = document.querySelector('[data-testid="loading-title"]');
      expect(titleSection).toBeTruthy();
    });

    it('should hide title skeleton when showTitle is false', () => {
      render(<PageLoadingState showTitle={false} />);
      const titleSection = document.querySelector('[data-testid="loading-title"]');
      expect(titleSection).toBeNull();
    });
  });

  describe('Description Section', () => {
    it('should show description skeleton by default', () => {
      render(<PageLoadingState />);
      const descSection = document.querySelector('[data-testid="loading-description"]');
      expect(descSection).toBeTruthy();
    });

    it('should hide description skeleton when showDescription is false', () => {
      render(<PageLoadingState showDescription={false} />);
      const descSection = document.querySelector('[data-testid="loading-description"]');
      expect(descSection).toBeNull();
    });
  });

  describe('Custom Class Names', () => {
    it('should apply custom className to container', () => {
      render(<PageLoadingState className="custom-class" />);
      const container = document.querySelector('.custom-class');
      expect(container).toBeTruthy();
    });

    it('should merge custom className with default classes', () => {
      render(<PageLoadingState className="my-custom-class" />);
      const container = document.querySelector('.my-custom-class');
      expect(container?.className).toContain('space-y');
    });
  });

  describe('Skeleton Heights', () => {
    it('should use default skeleton height', () => {
      render(<PageLoadingState />);
      const items = document.querySelectorAll('[data-testid="loading-items"] [class*="skeleton"]');
      items.forEach((item) => {
        expect(item.className).toMatch(/h-\d+|h-\[\d+/);
      });
    });

    it('should apply custom item height', () => {
      render(<PageLoadingState itemHeight="h-48" />);
      const items = document.querySelectorAll('[data-testid="loading-items"] [class*="skeleton"]');
      items.forEach((item) => {
        expect(item.className).toContain('h-48');
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('should have responsive grid columns for cards layout', () => {
      render(<PageLoadingState layout="cards" />);
      const container = document.querySelector('[data-testid="loading-items"]');
      // Should have responsive classes like md:grid-cols-2 lg:grid-cols-4
      expect(container?.className).toMatch(/md:grid-cols|lg:grid-cols/);
    });

    it('should have responsive grid columns for grid layout', () => {
      render(<PageLoadingState layout="grid" />);
      const container = document.querySelector('[data-testid="loading-items"]');
      expect(container?.className).toMatch(/md:grid-cols|lg:grid-cols/);
    });
  });

  describe('Animation', () => {
    it('should have animation class on skeletons', () => {
      render(<PageLoadingState />);
      const skeleton = document.querySelector('[class*="skeleton"]');
      // Skeleton component should have animate-pulse or similar
      expect(skeleton?.className).toMatch(/animate|skeleton/);
    });
  });
});

