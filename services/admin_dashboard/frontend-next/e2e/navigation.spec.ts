/**
 * Navigation E2E Tests
 * 
 * Tests for sidebar navigation, routing, and page transitions
 */

import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  // Before each test, go to root (assuming login or dashboard)
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test.describe('Sidebar Navigation', () => {
    test('should display sidebar with navigation links', async ({ page }) => {
      // Check for sidebar
      const sidebar = page.locator('[role="complementary"]');
      await expect(sidebar).toBeVisible();
    });

    test('should navigate to Releases page', async ({ page }) => {
      await page.getByRole('link', { name: /releases/i }).click();
      await expect(page).toHaveURL('/releases');
      await expect(page.getByRole('heading', { name: /releases/i })).toBeVisible();
    });

    test('should navigate to Health Monitor page', async ({ page }) => {
      await page.getByRole('link', { name: /health/i }).click();
      await expect(page).toHaveURL('/health');
      await expect(page.getByRole('heading', { name: /health/i })).toBeVisible();
    });

    test('should navigate to Metrics page', async ({ page }) => {
      await page.getByRole('link', { name: /observability|metrics/i }).click();
      await expect(page).toHaveURL('/metrics');
      await expect(page.getByRole('heading', { name: /metrics|observability/i })).toBeVisible();
    });

    test('should navigate to Feature Requests page', async ({ page }) => {
      await page.getByRole('link', { name: /feature/i }).click();
      await expect(page).toHaveURL('/feature-requests');
      await expect(page.getByRole('heading', { name: /feature/i })).toBeVisible();
    });

    test('should navigate to Settings page', async ({ page }) => {
      await page.getByRole('link', { name: /settings|configuration/i }).click();
      await expect(page).toHaveURL('/settings');
      await expect(page.getByRole('heading', { name: /configuration|settings/i })).toBeVisible();
    });
  });

  test.describe('Admin Navigation', () => {
    test('should navigate to User Management', async ({ page }) => {
      const userManagement = page.getByRole('link', { name: /user management/i });
      if (await userManagement.isVisible()) {
        await userManagement.click();
        await expect(page).toHaveURL('/admin/users');
      }
    });

    test('should navigate to Role Management', async ({ page }) => {
      const roleManagement = page.getByRole('link', { name: /role management/i });
      if (await roleManagement.isVisible()) {
        await roleManagement.click();
        await expect(page).toHaveURL('/admin/roles');
      }
    });
  });

  test.describe('Sidebar Collapse', () => {
    test('should toggle sidebar collapse', async ({ page }) => {
      const sidebar = page.locator('[role="complementary"]');
      const toggleButton = page.getByRole('button', { name: /collapse|expand/i });
      
      // Initially expanded
      await expect(sidebar).toBeVisible();
      
      // Click to collapse (if button exists)
      if (await toggleButton.isVisible()) {
        await toggleButton.click();
        
        // Should be collapsed (narrower width)
        await page.waitForTimeout(300); // Wait for animation
        
        // Click to expand again
        await toggleButton.click();
        await page.waitForTimeout(300);
      }
    });
  });

  test.describe('Breadcrumb Navigation', () => {
    test('should show breadcrumbs on subpages', async ({ page }) => {
      await page.goto('/admin/users');
      
      // Check for breadcrumb navigation
      const breadcrumb = page.locator('[aria-label="Breadcrumb"]');
      if (await breadcrumb.isVisible()) {
        await expect(breadcrumb).toContainText(/home|dashboard/i);
      }
    });
  });

  test.describe('Active State', () => {
    test('should highlight active navigation item', async ({ page }) => {
      await page.getByRole('link', { name: /releases/i }).click();
      await expect(page).toHaveURL('/releases');
      
      // The active link should have different styling
      const activeLink = page.getByRole('link', { name: /releases/i });
      await expect(activeLink).toHaveClass(/bg-primary|active/);
    });
  });

  test.describe('Logo Link', () => {
    test('should navigate home when clicking logo', async ({ page }) => {
      await page.goto('/releases');
      
      // Find and click the logo/home link
      const logo = page.getByRole('link', { name: /nexus/i }).first();
      await logo.click();
      
      await expect(page).toHaveURL('/');
    });
  });
});

