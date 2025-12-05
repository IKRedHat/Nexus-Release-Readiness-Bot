/**
 * Skeleton Component Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Skeleton } from '../skeleton';

describe('Skeleton', () => {
  describe('Rendering', () => {
    it('should render skeleton element', () => {
      render(<Skeleton data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton')).toBeInTheDocument();
    });

    it('should render as div', () => {
      const { container } = render(<Skeleton />);
      expect(container.querySelector('div')).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should have animate-pulse class', () => {
      render(<Skeleton data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton').className).toContain('animate-pulse');
    });

    it('should have rounded corners', () => {
      render(<Skeleton data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton').className).toContain('rounded-md');
    });

    it('should have muted background', () => {
      render(<Skeleton data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton').className).toContain('bg-muted');
    });

    it('should apply custom className', () => {
      render(<Skeleton className="w-full h-4" data-testid="skeleton" />);
      const skeleton = screen.getByTestId('skeleton');
      expect(skeleton.className).toContain('w-full');
      expect(skeleton.className).toContain('h-4');
    });

    it('should preserve base classes when adding custom classes', () => {
      render(<Skeleton className="custom-class" data-testid="skeleton" />);
      const skeleton = screen.getByTestId('skeleton');
      expect(skeleton.className).toContain('animate-pulse');
      expect(skeleton.className).toContain('rounded-md');
      expect(skeleton.className).toContain('bg-muted');
      expect(skeleton.className).toContain('custom-class');
    });
  });

  describe('Sizing', () => {
    it('should render with custom width', () => {
      render(<Skeleton className="w-64" data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton').className).toContain('w-64');
    });

    it('should render with custom height', () => {
      render(<Skeleton className="h-8" data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton').className).toContain('h-8');
    });

    it('should render as square', () => {
      render(<Skeleton className="w-10 h-10" data-testid="skeleton" />);
      const skeleton = screen.getByTestId('skeleton');
      expect(skeleton.className).toContain('w-10');
      expect(skeleton.className).toContain('h-10');
    });

    it('should render as circle', () => {
      render(<Skeleton className="w-12 h-12 rounded-full" data-testid="skeleton" />);
      const skeleton = screen.getByTestId('skeleton');
      expect(skeleton.className).toContain('w-12');
      expect(skeleton.className).toContain('h-12');
      expect(skeleton.className).toContain('rounded-full');
    });
  });

  describe('Use Cases', () => {
    it('should render text line skeleton', () => {
      render(<Skeleton className="h-4 w-[250px]" data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton')).toBeInTheDocument();
    });

    it('should render avatar skeleton', () => {
      render(<Skeleton className="h-12 w-12 rounded-full" data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton').className).toContain('rounded-full');
    });

    it('should render button skeleton', () => {
      render(<Skeleton className="h-10 w-24" data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton')).toBeInTheDocument();
    });

    it('should render card skeleton', () => {
      render(
        <div data-testid="card-skeleton" className="flex flex-col space-y-3">
          <Skeleton className="h-[125px] w-[250px] rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-4 w-[200px]" />
          </div>
        </div>
      );
      const container = screen.getByTestId('card-skeleton');
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons).toHaveLength(3);
    });
  });

  describe('Composed Skeletons', () => {
    it('should render multiple skeletons', () => {
      render(
        <div data-testid="skeleton-group">
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      );
      const skeletons = screen.getByTestId('skeleton-group').querySelectorAll('.animate-pulse');
      expect(skeletons).toHaveLength(3);
    });

    it('should render skeleton with different animations', () => {
      render(
        <div data-testid="skeleton-container">
          <Skeleton className="h-4" data-testid="skeleton-1" />
          <Skeleton className="h-4" data-testid="skeleton-2" />
        </div>
      );
      
      // Both should have animation class
      expect(screen.getByTestId('skeleton-1').className).toContain('animate-pulse');
      expect(screen.getByTestId('skeleton-2').className).toContain('animate-pulse');
    });
  });

  describe('HTML Attributes', () => {
    it('should pass through HTML attributes', () => {
      render(<Skeleton data-testid="skeleton" aria-hidden="true" role="presentation" />);
      const skeleton = screen.getByTestId('skeleton');
      expect(skeleton).toHaveAttribute('aria-hidden', 'true');
      expect(skeleton).toHaveAttribute('role', 'presentation');
    });

    it('should support style prop', () => {
      render(<Skeleton style={{ width: '200px' }} data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton')).toHaveStyle({ width: '200px' });
    });
  });

  describe('Accessibility', () => {
    it('should support aria-busy for loading state', () => {
      render(<Skeleton aria-busy="true" data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton')).toHaveAttribute('aria-busy', 'true');
    });

    it('should be hidden from screen readers when decorative', () => {
      render(<Skeleton aria-hidden="true" data-testid="skeleton" />);
      expect(screen.getByTestId('skeleton')).toHaveAttribute('aria-hidden', 'true');
    });
  });
});

