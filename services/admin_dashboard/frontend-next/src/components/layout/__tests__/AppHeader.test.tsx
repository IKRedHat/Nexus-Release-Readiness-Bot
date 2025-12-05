/**
 * AppHeader Component Tests
 * 
 * TDD: Tests written BEFORE implementation
 * 
 * The AppHeader is the top navigation bar that displays:
 * - Welcome message
 * - System status indicator
 * - Optional notifications
 * - Search (optional)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AppHeader } from '../AppHeader';

describe('AppHeader', () => {
  const mockUser = {
    id: 'user-1',
    name: 'John Doe',
    email: 'john@example.com',
    roles: ['admin'],
    permissions: ['*'],
    is_admin: true,
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(<AppHeader />);
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('should render welcome message with user name', () => {
      render(<AppHeader user={mockUser} />);
      expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
      expect(screen.getByText(/john doe/i)).toBeInTheDocument();
    });

    it('should render generic welcome when no user', () => {
      render(<AppHeader />);
      expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    });
  });

  describe('System Status', () => {
    it('should show system healthy status by default', () => {
      render(<AppHeader />);
      expect(screen.getByText(/healthy/i)).toBeInTheDocument();
    });

    it('should show custom status when provided', () => {
      render(<AppHeader systemStatus="degraded" />);
      expect(screen.getByText(/degraded/i)).toBeInTheDocument();
    });

    it('should show status indicator dot', () => {
      render(<AppHeader systemStatus="healthy" />);
      const indicator = document.querySelector('[data-testid="status-indicator"]');
      expect(indicator).toBeTruthy();
      expect(indicator?.className).toContain('bg-green');
    });

    it('should show yellow indicator for degraded status', () => {
      render(<AppHeader systemStatus="degraded" />);
      const indicator = document.querySelector('[data-testid="status-indicator"]');
      expect(indicator?.className).toContain('yellow');
    });

    it('should show red indicator for down status', () => {
      render(<AppHeader systemStatus="down" />);
      const indicator = document.querySelector('[data-testid="status-indicator"]');
      expect(indicator?.className).toContain('red');
    });
  });

  describe('Search', () => {
    it('should not show search by default', () => {
      render(<AppHeader />);
      expect(screen.queryByRole('search')).not.toBeInTheDocument();
    });

    it('should show search when showSearch is true', () => {
      render(<AppHeader showSearch />);
      expect(screen.getByRole('search')).toBeInTheDocument();
    });

    it('should call onSearch when search is submitted', () => {
      const onSearch = vi.fn();
      render(<AppHeader showSearch onSearch={onSearch} />);
      
      const searchInput = screen.getByPlaceholderText(/search/i);
      fireEvent.change(searchInput, { target: { value: 'test query' } });
      fireEvent.submit(searchInput.closest('form')!);
      
      expect(onSearch).toHaveBeenCalledWith('test query');
    });
  });

  describe('Notifications', () => {
    it('should not show notifications by default', () => {
      render(<AppHeader />);
      expect(screen.queryByRole('button', { name: /notification/i })).not.toBeInTheDocument();
    });

    it('should show notification bell when showNotifications is true', () => {
      render(<AppHeader showNotifications />);
      expect(screen.getByRole('button', { name: /notification/i })).toBeInTheDocument();
    });

    it('should show notification count badge', () => {
      render(<AppHeader showNotifications notificationCount={5} />);
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('should not show badge when count is 0', () => {
      render(<AppHeader showNotifications notificationCount={0} />);
      expect(screen.queryByText('0')).not.toBeInTheDocument();
    });

    it('should show 99+ for large counts', () => {
      render(<AppHeader showNotifications notificationCount={150} />);
      expect(screen.getByText('99+')).toBeInTheDocument();
    });

    it('should call onNotificationClick when bell is clicked', () => {
      const onClick = vi.fn();
      render(<AppHeader showNotifications onNotificationClick={onClick} />);
      
      const bellButton = screen.getByRole('button', { name: /notification/i });
      fireEvent.click(bellButton);
      
      expect(onClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Breadcrumbs', () => {
    it('should not show breadcrumbs by default', () => {
      render(<AppHeader />);
      expect(screen.queryByRole('navigation', { name: /breadcrumb/i })).not.toBeInTheDocument();
    });

    it('should show breadcrumbs when provided', () => {
      render(
        <AppHeader 
          breadcrumbs={[
            { label: 'Home', href: '/' },
            { label: 'Settings' },
          ]}
        />
      );
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    it('should render custom actions', () => {
      render(
        <AppHeader 
          actions={<button data-testid="custom-action">Custom</button>}
        />
      );
      expect(screen.getByTestId('custom-action')).toBeInTheDocument();
    });
  });

  describe('Layout', () => {
    it('should have proper height', () => {
      render(<AppHeader />);
      const header = screen.getByRole('banner');
      expect(header.className).toContain('h-16');
    });

    it('should have border bottom', () => {
      render(<AppHeader />);
      const header = screen.getByRole('banner');
      expect(header.className).toContain('border-b');
    });

    it('should have flex layout', () => {
      render(<AppHeader />);
      const header = screen.getByRole('banner');
      expect(header.className).toContain('flex');
    });
  });

  describe('Accessibility', () => {
    it('should have role="banner"', () => {
      render(<AppHeader />);
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('should have accessible search input', () => {
      render(<AppHeader showSearch />);
      const searchInput = screen.getByRole('searchbox');
      expect(searchInput).toHaveAttribute('aria-label');
    });
  });

  describe('Styling', () => {
    it('should apply custom className', () => {
      render(<AppHeader className="custom-class" />);
      const header = screen.getByRole('banner');
      expect(header.className).toContain('custom-class');
    });
  });

  describe('Theme', () => {
    it('should show theme toggle when showThemeToggle is true', () => {
      render(<AppHeader showThemeToggle />);
      expect(screen.getByRole('button', { name: /theme/i })).toBeInTheDocument();
    });

    it('should call onThemeToggle when clicked', () => {
      const onThemeToggle = vi.fn();
      render(<AppHeader showThemeToggle onThemeToggle={onThemeToggle} />);
      
      const themeButton = screen.getByRole('button', { name: /theme/i });
      fireEvent.click(themeButton);
      
      expect(onThemeToggle).toHaveBeenCalledTimes(1);
    });
  });
});

