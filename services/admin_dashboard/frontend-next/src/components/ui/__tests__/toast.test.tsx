/**
 * Toast Component Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { ToastProvider, useToast } from '../toast';
import { Button } from '../button';

// Test component that uses the toast hook
function TestComponent() {
  const { success, error, warning, info, toasts } = useToast();
  
  return (
    <div>
      <Button onClick={() => success('Success!', 'Operation completed')}>Success</Button>
      <Button onClick={() => error('Error!', 'Something went wrong')}>Error</Button>
      <Button onClick={() => warning('Warning!', 'Be careful')}>Warning</Button>
      <Button onClick={() => info('Info!', 'FYI')}>Info</Button>
      <div data-testid="toast-count">{toasts.length}</div>
    </div>
  );
}

describe('Toast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('ToastProvider', () => {
    it('should render children', () => {
      render(
        <ToastProvider>
          <div data-testid="child">Child content</div>
        </ToastProvider>
      );
      
      expect(screen.getByTestId('child')).toBeInTheDocument();
    });

    it('should throw error when useToast is used outside provider', () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(() => {
        render(<TestComponent />);
      }).toThrow('useToast must be used within a ToastProvider');
      
      consoleError.mockRestore();
    });
  });

  describe('Toast Types', () => {
    it('should show success toast', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /success/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Success!')).toBeInTheDocument();
        expect(screen.getByText('Operation completed')).toBeInTheDocument();
      });
    });

    it('should show error toast', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /^error$/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Error!')).toBeInTheDocument();
        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      });
    });

    it('should show warning toast', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /warning/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Warning!')).toBeInTheDocument();
        expect(screen.getByText('Be careful')).toBeInTheDocument();
      });
    });

    it('should show info toast', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /^info$/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Info!')).toBeInTheDocument();
        expect(screen.getByText('FYI')).toBeInTheDocument();
      });
    });
  });

  describe('Toast Behavior', () => {
    it('should auto-dismiss after duration', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /success/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Success!')).toBeInTheDocument();
      });
      
      // Fast forward past the duration
      act(() => {
        vi.advanceTimersByTime(6000);
      });
      
      await waitFor(() => {
        expect(screen.queryByText('Success!')).not.toBeInTheDocument();
      });
    });

    it('should allow manual dismissal', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /success/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Success!')).toBeInTheDocument();
      });
      
      // Click dismiss button
      const dismissButton = screen.getByRole('button', { name: /dismiss/i });
      fireEvent.click(dismissButton);
      
      await waitFor(() => {
        expect(screen.queryByText('Success!')).not.toBeInTheDocument();
      });
    });

    it('should show multiple toasts', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /success/i }));
      fireEvent.click(screen.getByRole('button', { name: /^error$/i }));
      fireEvent.click(screen.getByRole('button', { name: /warning/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Success!')).toBeInTheDocument();
        expect(screen.getByText('Error!')).toBeInTheDocument();
        expect(screen.getByText('Warning!')).toBeInTheDocument();
      });
    });

    it('should update toast count', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      expect(screen.getByTestId('toast-count')).toHaveTextContent('0');
      
      fireEvent.click(screen.getByRole('button', { name: /success/i }));
      
      await waitFor(() => {
        expect(screen.getByTestId('toast-count')).toHaveTextContent('1');
      });
      
      fireEvent.click(screen.getByRole('button', { name: /^error$/i }));
      
      await waitFor(() => {
        expect(screen.getByTestId('toast-count')).toHaveTextContent('2');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have alert role', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /success/i }));
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    it('should have notifications region', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /success/i }));
      
      await waitFor(() => {
        expect(screen.getByRole('region', { name: /notifications/i })).toBeInTheDocument();
      });
    });

    it('should have aria-live polite', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /success/i }));
      
      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toHaveAttribute('aria-live', 'polite');
      });
    });
  });

  describe('Toast Styling', () => {
    it('should have correct test id for success', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /success/i }));
      
      await waitFor(() => {
        expect(screen.getByTestId('toast-success')).toBeInTheDocument();
      });
    });

    it('should have correct test id for error', async () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /^error$/i }));
      
      await waitFor(() => {
        expect(screen.getByTestId('toast-error')).toBeInTheDocument();
      });
    });
  });
});

