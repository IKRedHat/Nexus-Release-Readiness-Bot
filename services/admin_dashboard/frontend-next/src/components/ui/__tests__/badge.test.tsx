/**
 * Badge Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '../badge';

describe('Badge', () => {
  describe('Rendering', () => {
    it('should render badge with text', () => {
      render(<Badge>Active</Badge>);
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('should render children', () => {
      render(<Badge><span data-testid="icon">✓</span> Done</Badge>);
      expect(screen.getByTestId('icon')).toBeInTheDocument();
      expect(screen.getByText('Done')).toBeInTheDocument();
    });

    it('should forward ref', () => {
      const ref = vi.fn();
      render(<Badge ref={ref}>Badge</Badge>);
      expect(ref).toHaveBeenCalled();
    });
  });

  describe('Variants', () => {
    it('should render default variant', () => {
      render(<Badge variant="default">Default</Badge>);
      const badge = screen.getByText('Default');
      expect(badge.className).toContain('bg-primary/10');
      expect(badge.className).toContain('text-primary');
    });

    it('should render success variant', () => {
      render(<Badge variant="success">Success</Badge>);
      const badge = screen.getByText('Success');
      expect(badge.className).toContain('bg-green-500/10');
      expect(badge.className).toContain('text-green-500');
    });

    it('should render warning variant', () => {
      render(<Badge variant="warning">Warning</Badge>);
      const badge = screen.getByText('Warning');
      expect(badge.className).toContain('bg-yellow-500/10');
      expect(badge.className).toContain('text-yellow-500');
    });

    it('should render danger variant', () => {
      render(<Badge variant="danger">Danger</Badge>);
      const badge = screen.getByText('Danger');
      expect(badge.className).toContain('bg-red-500/10');
      expect(badge.className).toContain('text-red-500');
    });

    it('should render info variant', () => {
      render(<Badge variant="info">Info</Badge>);
      const badge = screen.getByText('Info');
      expect(badge.className).toContain('bg-blue-500/10');
      expect(badge.className).toContain('text-blue-500');
    });

    it('should render outline variant', () => {
      render(<Badge variant="outline">Outline</Badge>);
      const badge = screen.getByText('Outline');
      expect(badge.className).toContain('bg-transparent');
      expect(badge.className).toContain('text-foreground');
    });
  });

  describe('Styling', () => {
    it('should have rounded-full class', () => {
      render(<Badge>Rounded</Badge>);
      expect(screen.getByText('Rounded').className).toContain('rounded-full');
    });

    it('should have border class', () => {
      render(<Badge>Bordered</Badge>);
      expect(screen.getByText('Bordered').className).toContain('border');
    });

    it('should have appropriate padding', () => {
      render(<Badge>Padded</Badge>);
      const badge = screen.getByText('Padded');
      expect(badge.className).toContain('px-2.5');
      expect(badge.className).toContain('py-0.5');
    });

    it('should have font styles', () => {
      render(<Badge>Styled</Badge>);
      const badge = screen.getByText('Styled');
      expect(badge.className).toContain('text-xs');
      expect(badge.className).toContain('font-semibold');
    });

    it('should apply custom className', () => {
      render(<Badge className="custom-badge">Custom</Badge>);
      expect(screen.getByText('Custom').className).toContain('custom-badge');
    });
  });

  describe('Accessibility', () => {
    it('should be rendered as div by default', () => {
      const { container } = render(<Badge>Badge</Badge>);
      expect(container.querySelector('div')).toBeInTheDocument();
    });

    it('should support data attributes', () => {
      render(<Badge data-testid="status-badge">Status</Badge>);
      expect(screen.getByTestId('status-badge')).toBeInTheDocument();
    });
  });

  describe('Use Cases', () => {
    it('should display status with icon', () => {
      render(
        <Badge variant="success">
          <span>●</span>
          <span> Active</span>
        </Badge>
      );
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('should work as count indicator', () => {
      render(<Badge variant="danger">99+</Badge>);
      expect(screen.getByText('99+')).toBeInTheDocument();
    });
  });
});

