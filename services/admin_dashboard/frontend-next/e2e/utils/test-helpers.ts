import { Page, expect } from '@playwright/test';

/**
 * E2E Test Utilities
 * 
 * Common functions used across E2E tests for the Nexus Admin Dashboard.
 * These helpers provide reusable functionality for common test scenarios.
 */

/**
 * Login to the application with credentials
 */
export async function login(
  page: Page, 
  email = 'admin@nexus.dev', 
  password = 'nexus'
): Promise<void> {
  await page.goto('/login');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  
  // Wait for navigation away from login
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
}

/**
 * Wait for page to finish loading (no loading states visible)
 */
export async function waitForPageLoad(page: Page): Promise<void> {
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
export async function navigateTo(page: Page, path: string): Promise<void> {
  await page.goto(path);
  await waitForPageLoad(page);
}

/**
 * Check page has expected title in h1
 */
export async function expectPageTitle(page: Page, title: string | RegExp): Promise<void> {
  const heading = page.locator('h1');
  await expect(heading).toContainText(title);
}

/**
 * Click a navigation item by label and wait for navigation
 */
export async function clickNavItem(page: Page, label: string): Promise<void> {
  const navItem = page.locator(`nav a:has-text("${label}")`);
  await navItem.click();
  await waitForPageLoad(page);
}

/**
 * Logout from the application
 */
export async function logout(page: Page): Promise<void> {
  const logoutButton = page.locator('[title="Logout"]').or(
    page.locator('button:has(svg[class*="log-out"])')
  );
  await logoutButton.click();
  await page.waitForURL('/login');
}

/**
 * Check if user appears to be logged in
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  const userProfile = page.locator('[title="Logout"]');
  return userProfile.isVisible().catch(() => false);
}

/**
 * Click retry button on error state
 */
export async function clickRetry(page: Page): Promise<void> {
  const retryButton = page.locator('button:has-text("Retry")');
  await retryButton.click();
  await waitForPageLoad(page);
}

/**
 * Check if page is in loading state
 */
export async function isLoading(page: Page): Promise<boolean> {
  const skeleton = page.locator('[class*="skeleton"]');
  return skeleton.isVisible().catch(() => false);
}

/**
 * Mock API response for testing
 */
export async function mockAPIResponse(
  page: Page, 
  urlPattern: string, 
  response: object
): Promise<void> {
  await page.route(`**${urlPattern}**`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

/**
 * Mock API error for testing error states
 */
export async function mockAPIError(
  page: Page, 
  urlPattern: string, 
  statusCode = 500, 
  message = 'Internal Server Error'
): Promise<void> {
  await page.route(`**${urlPattern}**`, async (route) => {
    await route.fulfill({
      status: statusCode,
      contentType: 'application/json',
      body: JSON.stringify({ detail: message }),
    });
  });
}

/**
 * Take a full-page screenshot with name
 */
export async function takeScreenshot(page: Page, name: string): Promise<void> {
  await page.screenshot({ 
    path: `test-results/screenshots/${name}.png`, 
    fullPage: true 
  });
}

/**
 * Check basic accessibility (landmarks and headings)
 */
export async function checkBasicA11y(page: Page): Promise<void> {
  // Check for main landmark
  const main = page.locator('main');
  await expect(main).toBeVisible();
  
  // Check for heading
  const heading = page.locator('h1');
  await expect(heading).toBeVisible();
}

/**
 * Wait for network to be idle (useful after actions)
 */
export async function waitForNetworkIdle(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle');
}

/**
 * Fill form fields by label
 */
export async function fillFormField(
  page: Page, 
  label: string, 
  value: string
): Promise<void> {
  const input = page.getByLabel(label);
  await input.fill(value);
}
