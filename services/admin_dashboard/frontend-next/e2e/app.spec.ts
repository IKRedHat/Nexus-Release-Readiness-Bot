/**
 * Nexus Admin Dashboard - Core E2E Tests
 * 
 * These tests verify the basic functionality of the application:
 * - Navigation between pages
 * - Authentication flow
 * - Core UI components
 */

import { test, expect } from '@playwright/test';
import { expectPageTitle, waitForPageLoad } from './utils/test-helpers';

test.describe('Application Core', () => {
  test.describe('Navigation', () => {
    test('should navigate to login page', async ({ page }) => {
      await page.goto('/login');
      await expect(page).toHaveTitle(/Nexus/);
      await expect(page.locator('h1')).toContainText('Welcome to Nexus');
    });

    test('should display login form elements', async ({ page }) => {
      await page.goto('/login');
      
      // Check for form elements
      await expect(page.locator('input[type="email"]')).toBeVisible();
      await expect(page.locator('input[type="password"]')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should have sidebar navigation on dashboard', async ({ page }) => {
      await page.goto('/');
      
      // Check sidebar exists
      const sidebar = page.locator('aside');
      await expect(sidebar).toBeVisible();
      
      // Check navigation items
      await expect(page.locator('nav')).toBeVisible();
    });
  });

  test.describe('Pages', () => {
    test('should load dashboard page', async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('h1')).toContainText('Dashboard');
    });

    test('should load releases page', async ({ page }) => {
      await page.goto('/releases');
      await expect(page.locator('h1')).toContainText('Releases');
    });

    test('should load health page', async ({ page }) => {
      await page.goto('/health');
      await expect(page.locator('h1')).toContainText('Health');
    });

    test('should load metrics page', async ({ page }) => {
      await page.goto('/metrics');
      await expect(page.locator('h1')).toContainText(/Metrics|Observability/);
    });

    test('should load feature requests page', async ({ page }) => {
      await page.goto('/feature-requests');
      await expect(page.locator('h1')).toContainText(/Feature/);
    });

    test('should load settings page', async ({ page }) => {
      await page.goto('/settings');
      await expect(page.locator('h1')).toContainText(/Settings|Configuration/);
    });
  });

  test.describe('Responsive Design', () => {
    test('should be responsive on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      
      // Page should still be visible
      await expect(page.locator('main')).toBeVisible();
    });

    test('should be responsive on tablet', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/');
      
      // Page should still be visible
      await expect(page.locator('main')).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should display error page for invalid route', async ({ page }) => {
      await page.goto('/invalid-route-that-does-not-exist');
      
      // Should show 404 or redirect
      const content = await page.content();
      const is404 = content.includes('404') || content.includes('not found') || content.includes('Not Found');
      const isRedirect = page.url().includes('/login') || page.url() === 'http://localhost:3000/';
      
      expect(is404 || isRedirect).toBeTruthy();
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper page structure', async ({ page }) => {
      await page.goto('/');
      
      // Check for main landmark
      await expect(page.locator('main')).toBeVisible();
      
      // Check for heading hierarchy
      const h1 = page.locator('h1');
      await expect(h1).toBeVisible();
    });

    test('should have visible focus indicators', async ({ page }) => {
      await page.goto('/login');
      
      // Tab to email field and check focus
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });
  });
});

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should have logo and branding', async ({ page }) => {
    // Check for Nexus branding
    await expect(page.locator('text=Nexus')).toBeVisible();
  });

  test('should have default credentials hint', async ({ page }) => {
    // Check for credential hint
    await expect(page.locator('text=admin@nexus.dev')).toBeVisible();
  });

  test('should toggle password visibility', async ({ page }) => {
    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput).toBeVisible();
    
    // Click the eye icon to show password
    const toggleButton = page.locator('button').filter({ has: page.locator('svg') }).last();
    await toggleButton.click();
    
    // Password should now be visible (type="text")
    const textInput = page.locator('input[autocomplete="current-password"]');
    const type = await textInput.getAttribute('type');
    expect(type).toBe('text');
  });

  test('should validate email format', async ({ page }) => {
    const emailInput = page.locator('input[type="email"]');
    await emailInput.fill('invalid-email');
    
    // Try to submit
    await page.click('button[type="submit"]');
    
    // Browser should show validation error (email field has native validation)
    const validity = await emailInput.evaluate((el: HTMLInputElement) => el.validity.valid);
    expect(validity).toBe(false);
  });

  test('should show loading state on submit', async ({ page }) => {
    await page.fill('input[type="email"]', 'admin@nexus.dev');
    await page.fill('input[type="password"]', 'password');
    
    // Click submit and check for loading indicator
    await page.click('button[type="submit"]');
    
    // Should show loading spinner or "Signing in..." text
    const submitButton = page.locator('button[type="submit"]');
    const buttonText = await submitButton.textContent();
    
    // Either shows loading text or the button should be disabled
    const isDisabled = await submitButton.isDisabled();
    expect(buttonText?.includes('Signing') || isDisabled).toBeTruthy();
  });
});

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display welcome message', async ({ page }) => {
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('should display stat cards', async ({ page }) => {
    // Wait for any content to load
    await page.waitForTimeout(1000);
    
    // Check for stat cards or loading skeletons
    const cards = page.locator('[class*="card"]');
    const hasCards = await cards.count() > 0;
    
    const skeletons = page.locator('[class*="skeleton"]');
    const hasSkeletons = await skeletons.count() > 0;
    
    expect(hasCards || hasSkeletons).toBeTruthy();
  });

  test('should have quick action buttons', async ({ page }) => {
    // Look for action buttons or loading state
    const quickActions = page.locator('text=Quick Actions').or(page.locator('[class*="skeleton"]'));
    await expect(quickActions.first()).toBeVisible({ timeout: 5000 });
  });
});

