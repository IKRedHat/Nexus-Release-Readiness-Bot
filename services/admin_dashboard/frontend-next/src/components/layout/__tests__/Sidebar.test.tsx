/**
 * Sidebar Component Tests
 * 
 * TDD: Tests written BEFORE implementation
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Sidebar } from '../Sidebar';
import { SidebarLogo } from '../SidebarLogo';
import { SidebarNav, NavItem } from '../SidebarNav';
import { SidebarUserProfile } from '../SidebarUserProfile';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: () => '/',
  useRouter: () => ({ push: vi.fn() }),
}));

describe('Sidebar', () => {
  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(<Sidebar>Content</Sidebar>);
      expect(screen.getByRole('complementary')).toBeInTheDocument();
    });

    it('should render children', () => {
      render(<Sidebar><div data-testid="child">Child Content</div></Sidebar>);
      expect(screen.getByTestId('child')).toBeInTheDocument();
    });

    it('should be expanded by default', () => {
      render(<Sidebar>Content</Sidebar>);
      const sidebar = screen.getByRole('complementary');
      expect(sidebar.className).toContain('w-64');
    });

    it('should be collapsed when collapsed prop is true', () => {
      render(<Sidebar collapsed>Content</Sidebar>);
      const sidebar = screen.getByRole('complementary');
      expect(sidebar.className).toContain('w-20');
    });
  });

  describe('Toggle Functionality', () => {
    it('should call onToggle when toggle button is clicked', () => {
      const onToggle = vi.fn();
      render(<Sidebar onToggle={onToggle}>Content</Sidebar>);
      
      const toggleButton = screen.getByRole('button', { name: /toggle|collapse|expand/i });
      fireEvent.click(toggleButton);
      
      expect(onToggle).toHaveBeenCalledTimes(1);
    });

    it('should show collapse icon when expanded', () => {
      render(<Sidebar>Content</Sidebar>);
      // X icon for collapsing
      const toggleButton = screen.getByRole('button', { name: /collapse/i });
      expect(toggleButton).toBeInTheDocument();
    });

    it('should show expand icon when collapsed', () => {
      render(<Sidebar collapsed>Content</Sidebar>);
      // Menu icon for expanding
      const toggleButton = screen.getByRole('button', { name: /expand/i });
      expect(toggleButton).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have role="complementary"', () => {
      render(<Sidebar>Content</Sidebar>);
      expect(screen.getByRole('complementary')).toBeInTheDocument();
    });

    it('should have aria-label', () => {
      render(<Sidebar>Content</Sidebar>);
      expect(screen.getByLabelText(/sidebar|navigation/i)).toBeInTheDocument();
    });
  });
});

describe('SidebarLogo', () => {
  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(<SidebarLogo />);
      expect(screen.getByText(/nexus/i)).toBeInTheDocument();
    });

    it('should show full branding when not collapsed', () => {
      render(<SidebarLogo collapsed={false} />);
      expect(screen.getByText(/nexus/i)).toBeInTheDocument();
      expect(screen.getByText(/admin dashboard/i)).toBeInTheDocument();
    });

    it('should show only icon when collapsed', () => {
      render(<SidebarLogo collapsed />);
      // Should have icon but not full text
      const logo = document.querySelector('[data-testid="sidebar-logo"]');
      expect(logo).toBeTruthy();
    });
  });

  describe('Link', () => {
    it('should link to home page', () => {
      render(<SidebarLogo />);
      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '/');
    });
  });
});

describe('SidebarNav', () => {
  const mockItems: NavItem[] = [
    { to: '/', icon: () => <span>Icon1</span>, label: 'Dashboard' },
    { to: '/releases', icon: () => <span>Icon2</span>, label: 'Releases' },
    { to: '/admin/users', icon: () => <span>Icon3</span>, label: 'Users', permission: 'users:view' },
  ];

  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(<SidebarNav items={mockItems} />);
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('should render all nav items', () => {
      render(<SidebarNav items={mockItems} />);
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Releases')).toBeInTheDocument();
    });

    it('should show labels when not collapsed', () => {
      render(<SidebarNav items={mockItems} collapsed={false} />);
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    it('should hide labels when collapsed', () => {
      render(<SidebarNav items={mockItems} collapsed />);
      // Labels should not be visible (but items should still exist for tooltip)
      const dashboard = screen.queryByText('Dashboard');
      expect(dashboard).not.toBeVisible();
    });
  });

  describe('Active State', () => {
    it('should highlight active item based on pathname', () => {
      render(<SidebarNav items={mockItems} />);
      const activeItem = screen.getByRole('link', { name: /dashboard/i });
      expect(activeItem.className).toContain('bg-primary');
    });
  });

  describe('Section Headers', () => {
    it('should render section title when provided', () => {
      render(<SidebarNav items={mockItems} title="Main Navigation" />);
      expect(screen.getByText('Main Navigation')).toBeInTheDocument();
    });

    it('should not render section title when collapsed', () => {
      render(<SidebarNav items={mockItems} title="Main Navigation" collapsed />);
      expect(screen.queryByText('Main Navigation')).not.toBeVisible();
    });
  });

  describe('Permissions', () => {
    it('should filter items based on permissions', () => {
      render(
        <SidebarNav 
          items={mockItems} 
          hasPermission={(perm) => perm !== 'users:view'}
        />
      );
      expect(screen.queryByText('Users')).not.toBeInTheDocument();
    });

    it('should show all items when hasPermission returns true', () => {
      render(
        <SidebarNav 
          items={mockItems} 
          hasPermission={() => true}
        />
      );
      expect(screen.getByText('Users')).toBeInTheDocument();
    });
  });

  describe('Tooltips', () => {
    it('should show tooltip on collapsed items', () => {
      render(<SidebarNav items={mockItems} collapsed />);
      const item = screen.getByRole('link', { name: /dashboard/i });
      expect(item).toHaveAttribute('title', 'Dashboard');
    });
  });
});

describe('SidebarUserProfile', () => {
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
      render(<SidebarUserProfile user={mockUser} onLogout={() => {}} />);
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    it('should display user name', () => {
      render(<SidebarUserProfile user={mockUser} onLogout={() => {}} />);
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    it('should display user email', () => {
      render(<SidebarUserProfile user={mockUser} onLogout={() => {}} />);
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
    });

    it('should display user initial in avatar', () => {
      render(<SidebarUserProfile user={mockUser} onLogout={() => {}} />);
      expect(screen.getByText('J')).toBeInTheDocument();
    });

    it('should show only avatar when collapsed', () => {
      render(<SidebarUserProfile user={mockUser} onLogout={() => {}} collapsed />);
      // Avatar should be visible
      expect(screen.getByText('J')).toBeInTheDocument();
      // Name should not be visible
      expect(screen.queryByText('John Doe')).not.toBeVisible();
    });
  });

  describe('Logout', () => {
    it('should render logout button', () => {
      render(<SidebarUserProfile user={mockUser} onLogout={() => {}} />);
      expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
    });

    it('should call onLogout when logout button is clicked', () => {
      const onLogout = vi.fn();
      render(<SidebarUserProfile user={mockUser} onLogout={onLogout} />);
      
      const logoutButton = screen.getByRole('button', { name: /logout/i });
      fireEvent.click(logoutButton);
      
      expect(onLogout).toHaveBeenCalledTimes(1);
    });
  });

  describe('Fallback', () => {
    it('should show fallback text when user has no name', () => {
      const userWithoutName = { ...mockUser, name: '' };
      render(<SidebarUserProfile user={userWithoutName} onLogout={() => {}} />);
      expect(screen.getByText('j')).toBeInTheDocument(); // First letter of email
    });

    it('should show placeholder when no user', () => {
      render(<SidebarUserProfile user={null} onLogout={() => {}} />);
      expect(screen.getByText('?')).toBeInTheDocument();
    });
  });
});

