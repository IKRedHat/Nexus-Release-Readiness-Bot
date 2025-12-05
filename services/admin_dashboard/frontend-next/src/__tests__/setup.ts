/**
 * Vitest Test Setup
 * 
 * This file runs before all tests and sets up:
 * - Jest DOM matchers for React Testing Library
 * - Global mocks for browser APIs
 * - MSW (Mock Service Worker) for API mocking
 */

import '@testing-library/jest-dom';
import { afterAll, afterEach, beforeAll, vi } from 'vitest';

// ============================================================================
// MOCK BROWSER APIs
// ============================================================================

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver
class ResizeObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

window.ResizeObserver = ResizeObserverMock;

// Mock IntersectionObserver
class IntersectionObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  root = null;
  rootMargin = '';
  thresholds = [];
}

window.IntersectionObserver = IntersectionObserverMock as any;

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock sessionStorage
Object.defineProperty(window, 'sessionStorage', {
  value: localStorageMock,
});

// Mock scrollTo
window.scrollTo = vi.fn();

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// ============================================================================
// MOCK NEXT.JS ROUTER
// ============================================================================

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

// ============================================================================
// MOCK ENVIRONMENT VARIABLES
// ============================================================================

vi.stubEnv('NEXT_PUBLIC_API_URL', 'http://localhost:8088');

// ============================================================================
// CLEANUP HOOKS
// ============================================================================

beforeAll(() => {
  // Setup before all tests
});

afterEach(() => {
  // Clear all mocks after each test
  vi.clearAllMocks();
  localStorageMock.clear();
});

afterAll(() => {
  // Cleanup after all tests
  vi.restoreAllMocks();
});

// ============================================================================
// TEST UTILITIES
// ============================================================================

/**
 * Wait for async operations to complete
 */
export const waitForAsync = () => new Promise((resolve) => setTimeout(resolve, 0));

/**
 * Create a mock user for testing
 */
export const createMockUser = (overrides = {}) => ({
  id: 'user-1',
  email: 'test@example.com',
  name: 'Test User',
  roles: ['user'],
  permissions: ['releases:view'],
  is_admin: false,
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

/**
 * Create a mock release for testing
 */
export const createMockRelease = (overrides = {}) => ({
  id: 'release-1',
  version: '1.0.0',
  name: 'Test Release',
  status: 'planned' as const,
  release_date: new Date().toISOString(),
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

/**
 * Create mock health service for testing
 */
export const createMockHealthService = (overrides = {}) => ({
  service: 'Test Service',
  status: 'healthy' as const,
  uptime: 99.9,
  uptime_percentage: 99.9,
  last_check: new Date().toISOString(),
  response_time: 50,
  ...overrides,
});

