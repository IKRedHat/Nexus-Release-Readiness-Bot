/**
 * PageErrorState Component Tests
 * 
 * TDD: Tests written BEFORE implementation
 * 
 * This component displays an error state with retry functionality.
 * Used when API calls fail or data cannot be loaded.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PageErrorState } from '../PageErrorState';

describe('PageErrorState', () => {
  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(<PageErrorState title="Error" message="Something went wrong" />);
      expect(screen.getByText('Error')).toBeInTheDocument();
    });

    it('should render the title', () => {
      render(<PageErrorState title="Unable to Load Data" message="Error" />);
      expect(screen.getByRole('heading')).toHaveTextContent('Unable to Load Data');
    });

    it('should render the message', () => {
      render(<PageErrorState title="Error" message="Could not fetch data from server" />);
      expect(screen.getByText('Could not fetch data from server')).toBeInTheDocument();
    });

    it('should render the error icon', () => {
      render(<PageErrorState title="Error" message="Message" />);
      // Icon should be present (AlertCircle or similar)
      const icon = document.querySelector('svg');
      expect(icon).toBeTruthy();
    });
  });

  describe('Retry Button', () => {
    it('should render retry button when onRetry is provided', () => {
      const onRetry = vi.fn();
      render(<PageErrorState title="Error" message="Message" onRetry={onRetry} />);
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('should not render retry button when onRetry is not provided', () => {
      render(<PageErrorState title="Error" message="Message" />);
      expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
    });

    it('should call onRetry when retry button is clicked', () => {
      const onRetry = vi.fn();
      render(<PageErrorState title="Error" message="Message" onRetry={onRetry} />);
      
      const retryButton = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryButton);
      
      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('should support custom retry button text', () => {
      const onRetry = vi.fn();
      render(
        <PageErrorState 
          title="Error" 
          message="Message" 
          onRetry={onRetry}
          retryText="Try Again"
        />
      );
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });
  });

  describe('Secondary Action', () => {
    it('should render secondary action when provided', () => {
      const onSecondaryAction = vi.fn();
      render(
        <PageErrorState 
          title="Error" 
          message="Message"
          onSecondaryAction={onSecondaryAction}
          secondaryActionText="Go Back"
        />
      );
      expect(screen.getByRole('button', { name: /go back/i })).toBeInTheDocument();
    });

    it('should call secondary action when clicked', () => {
      const onSecondaryAction = vi.fn();
      render(
        <PageErrorState 
          title="Error" 
          message="Message"
          onSecondaryAction={onSecondaryAction}
          secondaryActionText="Go Home"
        />
      );
      
      const button = screen.getByRole('button', { name: /go home/i });
      fireEvent.click(button);
      
      expect(onSecondaryAction).toHaveBeenCalledTimes(1);
    });
  });

  describe('Variants', () => {
    it('should apply default variant styles', () => {
      render(<PageErrorState title="Error" message="Message" />);
      const container = document.querySelector('[data-testid="error-state"]');
      expect(container).toBeTruthy();
    });

    it('should apply warning variant styles', () => {
      render(<PageErrorState title="Warning" message="Message" variant="warning" />);
      const container = document.querySelector('[data-testid="error-state"]');
      expect(container?.className).toContain('warning');
    });

    it('should apply info variant styles', () => {
      render(<PageErrorState title="Info" message="Message" variant="info" />);
      const container = document.querySelector('[data-testid="error-state"]');
      expect(container?.className).toContain('info');
    });

    it('should apply 404 variant styles', () => {
      render(<PageErrorState title="Not Found" message="Message" variant="not-found" />);
      const container = document.querySelector('[data-testid="error-state"]');
      expect(container?.className).toContain('not-found');
    });
  });

  describe('Icon Customization', () => {
    it('should use default error icon', () => {
      render(<PageErrorState title="Error" message="Message" />);
      const icon = document.querySelector('svg');
      expect(icon).toBeTruthy();
    });

    it('should render custom icon when provided', () => {
      const CustomIcon = () => <svg data-testid="custom-icon" />;
      render(<PageErrorState title="Error" message="Message" icon={<CustomIcon />} />);
      expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    });

    it('should not render icon when showIcon is false', () => {
      render(<PageErrorState title="Error" message="Message" showIcon={false} />);
      const container = document.querySelector('[data-testid="error-icon"]');
      expect(container).toBeNull();
    });
  });

  describe('Accessibility', () => {
    it('should have role="alert"', () => {
      render(<PageErrorState title="Error" message="Message" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('should have aria-live="polite"', () => {
      render(<PageErrorState title="Error" message="Message" />);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'polite');
    });

    it('should have accessible heading', () => {
      render(<PageErrorState title="Error Title" message="Message" />);
      const heading = screen.getByRole('heading');
      expect(heading).toHaveTextContent('Error Title');
    });

    it('should have proper button accessibility', () => {
      const onRetry = vi.fn();
      render(<PageErrorState title="Error" message="Message" onRetry={onRetry} />);
      const button = screen.getByRole('button');
      expect(button).toBeEnabled();
    });
  });

  describe('Layout', () => {
    it('should be centered by default', () => {
      render(<PageErrorState title="Error" message="Message" />);
      const container = document.querySelector('[data-testid="error-state"]');
      expect(container?.className).toContain('mx-auto');
    });

    it('should apply full width layout when specified', () => {
      render(<PageErrorState title="Error" message="Message" fullWidth />);
      const container = document.querySelector('[data-testid="error-state"]');
      expect(container?.className).not.toContain('max-w');
    });

    it('should apply compact layout when specified', () => {
      render(<PageErrorState title="Error" message="Message" compact />);
      const container = document.querySelector('[data-testid="error-state"]');
      // Compact should have smaller padding/margins
      expect(container?.className).toMatch(/p-\d|py-\d|px-\d/);
    });
  });

  describe('Custom Styling', () => {
    it('should apply custom className', () => {
      render(<PageErrorState title="Error" message="Message" className="custom-class" />);
      const container = document.querySelector('.custom-class');
      expect(container).toBeTruthy();
    });

    it('should merge custom className with default styles', () => {
      render(<PageErrorState title="Error" message="Message" className="my-custom" />);
      const container = document.querySelector('.my-custom');
      expect(container?.className).toContain('mx-auto');
    });
  });

  describe('Error Details', () => {
    it('should show error details when provided', () => {
      render(
        <PageErrorState 
          title="Error" 
          message="Message"
          errorDetails="Stack trace: Error at line 42"
        />
      );
      expect(screen.getByText(/stack trace/i)).toBeInTheDocument();
    });

    it('should hide error details by default until expanded', () => {
      render(
        <PageErrorState 
          title="Error" 
          message="Message"
          errorDetails="Detailed error info"
          showDetailsToggle
        />
      );
      // Details should be collapsible
      const toggleButton = screen.getByRole('button', { name: /details|more/i });
      expect(toggleButton).toBeInTheDocument();
    });

    it('should toggle error details visibility', () => {
      render(
        <PageErrorState 
          title="Error" 
          message="Message"
          errorDetails="Secret details"
          showDetailsToggle
        />
      );
      
      const toggleButton = screen.getByRole('button', { name: /details|more/i });
      fireEvent.click(toggleButton);
      
      expect(screen.getByText(/secret details/i)).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should handle empty title gracefully', () => {
      render(<PageErrorState title="" message="Message" />);
      const heading = screen.getByRole('heading');
      expect(heading).toBeInTheDocument();
    });

    it('should handle empty message gracefully', () => {
      render(<PageErrorState title="Error" message="" />);
      expect(screen.getByText('Error')).toBeInTheDocument();
    });
  });
});

