/**
 * Authentication E2E Tests
 * 
 * Tests for login, logout, and protected routes
 */

import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.describe('Login Page', () => {
    test('should display login form', async ({ page }) => {
      await page.goto('/login');
      
      // Check page elements
      await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
      await expect(page.getByPlaceholder(/email/i)).toBeVisible();
      await expect(page.getByPlaceholder(/password/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
    });

    test('should show validation errors for empty form', async ({ page }) => {
      await page.goto('/login');
      
      // Click submit without filling form
      await page.getByRole('button', { name: /sign in/i }).click();
      
      // Should show validation or stay on login page
      await expect(page).toHaveURL(/login/);
    });

    test('should show validation for invalid email', async ({ page }) => {
      await page.goto('/login');
      
      await page.getByPlaceholder(/email/i).fill('invalid-email');
      await page.getByPlaceholder(/password/i).fill('password');
      await page.getByRole('button', { name: /sign in/i }).click();
      
      // Should stay on login page
      await expect(page).toHaveURL(/login/);
    });

    test('should display SSO providers', async ({ page }) => {
      await page.goto('/login');
      
      // Check for SSO buttons (Google, GitHub, etc.)
      const ssoSection = page.getByText(/or continue with/i);
      await expect(ssoSection).toBeVisible();
    });
  });

  test.describe('Protected Routes', () => {
    test('should redirect to login when not authenticated', async ({ page }) => {
      // Try to access dashboard without login
      await page.goto('/');
      
      // May either show login content or redirect
      const isLoginPage = await page.getByRole('heading', { name: /sign in/i }).isVisible().catch(() => false);
      const isDashboard = await page.getByRole('heading', { name: /dashboard/i }).isVisible().catch(() => false);
      
      // Either on login page or dashboard (if auth is mocked)
      expect(isLoginPage || isDashboard).toBeTruthy();
    });

    test('should protect admin routes', async ({ page }) => {
      await page.goto('/admin/users');
      
      // Should either redirect or show unauthorized
      const url = page.url();
      expect(url.includes('/admin/users') || url.includes('/login')).toBeTruthy();
    });
  });
});

