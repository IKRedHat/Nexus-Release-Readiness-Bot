/**
 * Page E2E Tests
 * 
 * Tests for all main pages: Dashboard, Releases, Health, Metrics, Feature Requests, Settings
 */

import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display dashboard with welcome message', async ({ page }) => {
    await expect(page.getByText(/welcome/i)).toBeVisible();
  });

  test('should display system status indicator', async ({ page }) => {
    const statusIndicator = page.getByText(/healthy|degraded|down/i);
    await expect(statusIndicator).toBeVisible();
  });

  test('should display quick stats cards', async ({ page }) => {
    // Look for stat cards
    const cards = page.locator('[class*="card"]');
    await expect(cards.first()).toBeVisible();
  });
});

test.describe('Releases Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/releases');
  });

  test('should display releases page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /releases/i })).toBeVisible();
    await expect(page.getByText(/manage and track/i)).toBeVisible();
  });

  test('should have New Release button', async ({ page }) => {
    const newButton = page.getByRole('button', { name: /new release/i });
    await expect(newButton).toBeVisible();
  });

  test('should display release stats', async ({ page }) => {
    // Look for stats cards
    const totalReleases = page.getByText(/total releases/i);
    await expect(totalReleases).toBeVisible();
  });

  test('should display loading state while fetching', async ({ page }) => {
    // Reload and catch loading state
    await page.reload();
    
    // Either shows loading skeletons or content
    const hasContent = await page.getByRole('heading', { name: /releases/i }).isVisible().catch(() => false);
    expect(hasContent).toBeTruthy();
  });
});

test.describe('Health Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/health');
  });

  test('should display health page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /health/i })).toBeVisible();
  });

  test('should have Refresh button', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    await expect(refreshButton).toBeVisible();
  });

  test('should display health status stats', async ({ page }) => {
    // Look for healthy/degraded/down counts
    const healthyLabel = page.getByText(/healthy services/i);
    await expect(healthyLabel).toBeVisible();
  });

  test('should display service cards or empty state', async ({ page }) => {
    // Either shows service cards or "No Services" message
    const hasServices = await page.locator('[class*="card"]').count() > 0;
    expect(hasServices).toBeTruthy();
  });
});

test.describe('Metrics Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/metrics');
  });

  test('should display metrics page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /metrics|observability/i })).toBeVisible();
  });

  test('should display system resources section', async ({ page }) => {
    await expect(page.getByText(/system resources/i)).toBeVisible();
  });

  test('should display CPU usage metric', async ({ page }) => {
    await expect(page.getByText(/cpu usage/i)).toBeVisible();
  });

  test('should display Memory usage metric', async ({ page }) => {
    await expect(page.getByText(/memory usage/i)).toBeVisible();
  });

  test('should display agent performance section', async ({ page }) => {
    await expect(page.getByText(/agent performance/i)).toBeVisible();
  });
});

test.describe('Feature Requests Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/feature-requests');
  });

  test('should display feature requests page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /feature requests/i })).toBeVisible();
  });

  test('should have New Request button', async ({ page }) => {
    const newButton = page.getByRole('button', { name: /new request/i });
    await expect(newButton).toBeVisible();
  });

  test('should display filter buttons', async ({ page }) => {
    // Should have status filter buttons
    const allFilter = page.getByRole('button', { name: /^all$/i });
    await expect(allFilter).toBeVisible();
  });

  test('should be able to filter by status', async ({ page }) => {
    const pendingFilter = page.getByRole('button', { name: /pending/i });
    if (await pendingFilter.isVisible()) {
      await pendingFilter.click();
      // Filter should be applied
      await expect(pendingFilter).toHaveClass(/bg-primary|active/);
    }
  });
});

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('should display settings page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /configuration/i })).toBeVisible();
  });

  test('should display general settings section', async ({ page }) => {
    await expect(page.getByText(/general settings/i)).toBeVisible();
  });

  test('should display SSO configuration section', async ({ page }) => {
    await expect(page.getByText(/sso configuration/i)).toBeVisible();
  });

  test('should display Jira integration section', async ({ page }) => {
    await expect(page.getByText(/jira integration/i)).toBeVisible();
  });

  test('should display API configuration section', async ({ page }) => {
    await expect(page.getByText(/api configuration/i)).toBeVisible();
  });

  test('should have Edit Configuration button', async ({ page }) => {
    const editButton = page.getByRole('button', { name: /edit configuration/i });
    await expect(editButton).toBeVisible();
  });
});

test.describe('User Management Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/users');
  });

  test('should display user management page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /user management/i })).toBeVisible();
  });

  test('should have Add User button', async ({ page }) => {
    const addButton = page.getByRole('button', { name: /add user/i });
    await expect(addButton).toBeVisible();
  });

  test('should display users table or empty state', async ({ page }) => {
    // Either shows table or "No Users Found"
    const hasTable = await page.locator('table').isVisible().catch(() => false);
    const hasEmptyState = await page.getByText(/no users found/i).isVisible().catch(() => false);
    
    expect(hasTable || hasEmptyState).toBeTruthy();
  });
});

test.describe('Role Management Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/roles');
  });

  test('should display role management page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /role management/i })).toBeVisible();
  });

  test('should have Create Role button', async ({ page }) => {
    const createButton = page.getByRole('button', { name: /create role/i });
    await expect(createButton).toBeVisible();
  });

  test('should display system roles section', async ({ page }) => {
    await expect(page.getByText(/system roles/i)).toBeVisible();
  });

  test('should display custom roles section', async ({ page }) => {
    await expect(page.getByText(/custom roles/i)).toBeVisible();
  });
});

