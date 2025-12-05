import { Page, expect } from '@playwright/test';

/**
 * E2E Test Utilities
 * 
 * Common functions used across E2E tests for the Nexus Admin Dashboard
 */

/**
 * Login to the application
 */
export async function login(page: Page, email = 'admin@nexus.dev', password = 'nexus') {
  await page.goto('/login');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  
  // Wait for navigation to dashboard
  await page.waitForURL('/');
}

/**
 * Wait for page to finish loading (no loading states visible)
 */
export async function waitForPageLoad(page: Page) {
  // Wait for any skeletons to disappear
  await page.waitForSelector('[class*="skeleton"]', { state: 'hidden', timeout: 10000 }).catch(() => {
    // Skeleton might not exist, that's OK
  });
  
  // Wait for main content to be visible
  await page.waitForSelector('main', { state: 'visible' });
}

/**
 * Navigate to a page and wait for it to load
 */
export async function navigateTo(page: Page, path: string) {
  await page.goto(path);
  await waitForPageLoad(page);
}

/**
 * Check if the sidebar is visible
 */
export async function isSidebarVisible(page: Page): Promise<boolean> {
  const sidebar = page.locator('aside');
  return sidebar.isVisible();
}

/**
 * Toggle sidebar open/close
 */
export async function toggleSidebar(page: Page) {
  const toggleButton = page.locator('button').filter({ has: page.locator('svg') }).first();
  await toggleButton.click();
}

/**
 * Get all navigation items
 */
export async function getNavItems(page: Page) {
  const navLinks = page.locator('nav a');
  return navLinks.all();
}

/**
 * Click a navigation item by label
 */
export async function clickNavItem(page: Page, label: string) {
  const navItem = page.locator(`nav a:has-text("${label}")`);
  await navItem.click();
  await waitForPageLoad(page);
}

/**
 * Check if user is logged in by checking for user profile in sidebar
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  const userProfile = page.locator('aside').locator('text=User').or(page.locator('[title="Logout"]'));
  return userProfile.isVisible();
}

/**
 * Logout from the application
 */
export async function logout(page: Page) {
  const logoutButton = page.locator('[title="Logout"]').or(page.locator('button:has(svg[class*="log-out"])'));
  await logoutButton.click();
  await page.waitForURL('/login');
}

/**
 * Get error message from error state
 */
export async function getErrorMessage(page: Page): Promise<string | null> {
  const errorCard = page.locator('text="Unable to Load"').locator('..');
  if (await errorCard.isVisible()) {
    const message = await errorCard.locator('p').textContent();
    return message;
  }
  return null;
}

/**
 * Click retry button on error state
 */
export async function clickRetry(page: Page) {
  const retryButton = page.locator('button:has-text("Retry")');
  await retryButton.click();
}

/**
 * Check page has title
 */
export async function expectPageTitle(page: Page, title: string) {
  const heading = page.locator('h1');
  await expect(heading).toContainText(title);
}

/**
 * Check for loading state
 */
export async function isLoading(page: Page): Promise<boolean> {
  const skeleton = page.locator('[class*="skeleton"]');
  return skeleton.isVisible();
}

/**
 * Mock API response for testing
 */
export async function mockAPIResponse(page: Page, url: string, response: object) {
  await page.route(`**${url}**`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

/**
 * Mock API error for testing
 */
export async function mockAPIError(page: Page, url: string, statusCode = 500, message = 'Internal Server Error') {
  await page.route(`**${url}**`, async (route) => {
    await route.fulfill({
      status: statusCode,
      contentType: 'application/json',
      body: JSON.stringify({ detail: message }),
    });
  });
}

/**
 * Take screenshot with name
 */
export async function takeScreenshot(page: Page, name: string) {
  await page.screenshot({ path: `test-results/screenshots/${name}.png`, fullPage: true });
}

/**
 * Check accessibility of current page (basic checks)
 */
export async function checkBasicA11y(page: Page) {
  // Check for main landmark
  const main = page.locator('main');
  await expect(main).toBeVisible();
  
  // Check for heading
  const heading = page.locator('h1');
  await expect(heading).toBeVisible();
  
  // Check all images have alt text
  const images = page.locator('img');
  const imageCount = await images.count();
  for (let i = 0; i < imageCount; i++) {
    const img = images.nth(i);
    await expect(img).toHaveAttribute('alt');
  }
  
  // Check all buttons have accessible text
  const buttons = page.locator('button');
  const buttonCount = await buttons.count();
  for (let i = 0; i < buttonCount; i++) {
    const button = buttons.nth(i);
    const text = await button.textContent();
    const ariaLabel = await button.getAttribute('aria-label');
    const title = await button.getAttribute('title');
    
    // Button should have text content, aria-label, or title
    if (!text?.trim() && !ariaLabel && !title) {
      const hasIcon = await button.locator('svg').count();
      if (!hasIcon) {
        throw new Error(`Button at index ${i} has no accessible text`);
      }
    }
  }
}

