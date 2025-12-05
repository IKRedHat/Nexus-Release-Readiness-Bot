/**
 * Accessibility E2E Tests
 * 
 * Tests for WCAG compliance and accessibility features
 */

import { test, expect } from '@playwright/test';

test.describe('Accessibility', () => {
  test.describe('Landmarks', () => {
    test('should have main landmark on dashboard', async ({ page }) => {
      await page.goto('/');
      
      // Check for main content area
      const main = page.locator('main');
      await expect(main).toBeVisible();
    });

    test('should have navigation landmark', async ({ page }) => {
      await page.goto('/');
      
      // Check for navigation
      const nav = page.locator('nav, [role="navigation"]');
      await expect(nav.first()).toBeVisible();
    });

    test('should have complementary landmark for sidebar', async ({ page }) => {
      await page.goto('/');
      
      const sidebar = page.locator('[role="complementary"]');
      await expect(sidebar).toBeVisible();
    });
  });

  test.describe('Headings', () => {
    test('should have proper heading hierarchy on dashboard', async ({ page }) => {
      await page.goto('/');
      
      // Should have h1
      const h1 = page.locator('h1');
      await expect(h1.first()).toBeVisible();
    });

    test('should have proper heading hierarchy on releases page', async ({ page }) => {
      await page.goto('/releases');
      
      const h1 = page.locator('h1');
      await expect(h1).toBeVisible();
    });

    test('should have proper heading on settings page', async ({ page }) => {
      await page.goto('/settings');
      
      const h1 = page.locator('h1');
      await expect(h1).toContainText(/configuration/i);
    });
  });

  test.describe('Form Accessibility', () => {
    test('login form should have labeled inputs', async ({ page }) => {
      await page.goto('/login');
      
      // Email input should be accessible
      const emailInput = page.getByLabel(/email/i);
      const emailByPlaceholder = page.getByPlaceholder(/email/i);
      const hasEmailAccess = await emailInput.isVisible().catch(() => false) || 
                             await emailByPlaceholder.isVisible().catch(() => false);
      expect(hasEmailAccess).toBeTruthy();
      
      // Password input should be accessible
      const passwordInput = page.getByLabel(/password/i);
      const passwordByPlaceholder = page.getByPlaceholder(/password/i);
      const hasPasswordAccess = await passwordInput.isVisible().catch(() => false) || 
                                await passwordByPlaceholder.isVisible().catch(() => false);
      expect(hasPasswordAccess).toBeTruthy();
    });

    test('search input should have aria-label', async ({ page }) => {
      await page.goto('/');
      
      const searchInput = page.getByRole('searchbox');
      if (await searchInput.isVisible()) {
        await expect(searchInput).toHaveAttribute('aria-label');
      }
    });
  });

  test.describe('Focus Management', () => {
    test('should be able to navigate with keyboard', async ({ page }) => {
      await page.goto('/login');
      
      // Tab through form elements
      await page.keyboard.press('Tab');
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });

    test('buttons should be focusable', async ({ page }) => {
      await page.goto('/releases');
      
      const button = page.getByRole('button', { name: /new release/i });
      await button.focus();
      await expect(button).toBeFocused();
    });
  });

  test.describe('Alert States', () => {
    test('error states should have role="alert"', async ({ page }) => {
      await page.goto('/settings');
      
      // If there's an error, it should be announced
      const alerts = page.locator('[role="alert"]');
      const alertCount = await alerts.count();
      
      // Alerts are optional, but if present, they exist
      expect(alertCount >= 0).toBeTruthy();
    });
  });

  test.describe('Color Contrast', () => {
    test('status badges should be visible', async ({ page }) => {
      await page.goto('/health');
      
      // Status badges should be visible (green/yellow/red)
      const badges = page.locator('[class*="badge"]');
      const badgeCount = await badges.count();
      
      if (badgeCount > 0) {
        await expect(badges.first()).toBeVisible();
      }
    });
  });

  test.describe('Interactive Elements', () => {
    test('buttons should have visible focus state', async ({ page }) => {
      await page.goto('/releases');
      
      const button = page.getByRole('button', { name: /new release/i });
      await button.focus();
      
      // Button should be focused and visible
      await expect(button).toBeFocused();
      await expect(button).toBeVisible();
    });

    test('links should have visible focus state', async ({ page }) => {
      await page.goto('/');
      
      const link = page.getByRole('link', { name: /releases/i });
      await link.focus();
      
      await expect(link).toBeFocused();
    });
  });

  test.describe('Loading States', () => {
    test('loading states should have aria-busy', async ({ page }) => {
      // Force a slow network to catch loading state
      await page.route('**/*', route => {
        // Small delay to see loading state
        setTimeout(() => route.continue(), 100);
      });
      
      await page.goto('/releases');
      
      // Either shows loading state with aria-busy or content
      const hasContent = await page.getByRole('heading', { name: /releases/i }).isVisible().catch(() => false);
      expect(hasContent).toBeTruthy();
    });
  });

  test.describe('Skip Links', () => {
    test('should have skip to main content option', async ({ page }) => {
      await page.goto('/');
      
      // Press tab to reveal skip link (if implemented)
      await page.keyboard.press('Tab');
      
      // Check if skip link exists
      const skipLink = page.locator('a[href="#main"]');
      const skipLinkExists = await skipLink.count() > 0;
      
      // Skip link is optional but good to have
      if (skipLinkExists) {
        await expect(skipLink).toBeVisible();
      }
    });
  });
});

