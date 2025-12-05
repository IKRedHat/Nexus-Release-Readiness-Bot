/**
 * Unit Tests for Utility Functions
 * 
 * Tests for src/lib/utils.ts
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  cn,
  formatDate,
  formatRelativeTime,
  formatDateTime,
  getStatusColor,
  getStatusIcon,
  formatNumber,
  formatPercentage,
  formatBytes,
  truncate,
  capitalize,
  slugify,
  debounce,
  isValidEmail,
  isValidUrl,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  sortBy,
  filterBySearch,
  getLocalStorage,
  setLocalStorage,
  removeLocalStorage,
} from '@/lib/utils';

describe('Utils', () => {
  describe('cn (class names)', () => {
    it('should merge class names', () => {
      expect(cn('foo', 'bar')).toBe('foo bar');
    });

    it('should handle conditional classes', () => {
      expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz');
    });

    it('should merge Tailwind classes correctly', () => {
      expect(cn('p-4', 'p-8')).toBe('p-8');
    });

    it('should handle empty inputs', () => {
      expect(cn()).toBe('');
    });

    it('should handle undefined and null', () => {
      expect(cn('foo', undefined, null, 'bar')).toBe('foo bar');
    });
  });

  describe('Date formatting', () => {
    const testDate = new Date('2024-01-15T10:30:00Z');

    describe('formatDate', () => {
      it('should format date with default format', () => {
        const result = formatDate(testDate);
        expect(result).toMatch(/Jan 15, 2024/);
      });

      it('should format date with custom format', () => {
        const result = formatDate(testDate, 'yyyy-MM-dd');
        expect(result).toBe('2024-01-15');
      });

      it('should handle string dates', () => {
        const result = formatDate('2024-01-15T10:30:00Z');
        expect(result).toMatch(/Jan 15, 2024/);
      });
    });

    describe('formatRelativeTime', () => {
      it('should return relative time string', () => {
        const recentDate = new Date(Date.now() - 5 * 60 * 1000); // 5 minutes ago
        const result = formatRelativeTime(recentDate);
        expect(result).toMatch(/minutes? ago/);
      });
    });

    describe('formatDateTime', () => {
      it('should format datetime', () => {
        const result = formatDateTime(testDate);
        expect(result).toMatch(/Jan 15, 2024/);
        expect(result).toMatch(/\d{2}:\d{2}:\d{2}/);
      });
    });
  });

  describe('Status utilities', () => {
    describe('getStatusColor', () => {
      it('should return correct color for healthy status', () => {
        const result = getStatusColor('healthy');
        expect(result).toContain('green');
      });

      it('should return correct color for degraded status', () => {
        const result = getStatusColor('degraded');
        expect(result).toContain('yellow');
      });

      it('should return correct color for down status', () => {
        const result = getStatusColor('down');
        expect(result).toContain('red');
      });

      it('should return default color for unknown status', () => {
        const result = getStatusColor('unknown');
        expect(result).toContain('gray');
      });

      it('should be case-insensitive', () => {
        expect(getStatusColor('HEALTHY')).toContain('green');
        expect(getStatusColor('Healthy')).toContain('green');
      });
    });

    describe('getStatusIcon', () => {
      it('should return correct icon for healthy', () => {
        expect(getStatusIcon('healthy')).toBe('●');
      });

      it('should return correct icon for degraded', () => {
        expect(getStatusIcon('degraded')).toBe('◐');
      });

      it('should return default icon for unknown', () => {
        expect(getStatusIcon('unknown')).toBe('○');
      });
    });
  });

  describe('Number formatting', () => {
    describe('formatNumber', () => {
      it('should format small numbers as-is', () => {
        expect(formatNumber(100)).toBe('100');
        expect(formatNumber(999)).toBe('999');
      });

      it('should format thousands with K suffix', () => {
        expect(formatNumber(1000)).toBe('1.0K');
        expect(formatNumber(5500)).toBe('5.5K');
      });

      it('should format millions with M suffix', () => {
        expect(formatNumber(1000000)).toBe('1.0M');
        expect(formatNumber(2500000)).toBe('2.5M');
      });
    });

    describe('formatPercentage', () => {
      it('should format percentage with default decimals', () => {
        expect(formatPercentage(95.5)).toBe('95.5%');
      });

      it('should format percentage with custom decimals', () => {
        expect(formatPercentage(95.555, 2)).toBe('95.56%');
      });
    });

    describe('formatBytes', () => {
      it('should format bytes correctly', () => {
        expect(formatBytes(0)).toBe('0 Bytes');
        expect(formatBytes(1024)).toBe('1 KB');
        expect(formatBytes(1048576)).toBe('1 MB');
        expect(formatBytes(1073741824)).toBe('1 GB');
      });

      it('should handle custom decimal places', () => {
        expect(formatBytes(1536, 1)).toBe('1.5 KB');
      });
    });
  });

  describe('String utilities', () => {
    describe('truncate', () => {
      it('should truncate long strings', () => {
        expect(truncate('Hello World', 5)).toBe('Hello...');
      });

      it('should not truncate short strings', () => {
        expect(truncate('Hi', 10)).toBe('Hi');
      });
    });

    describe('capitalize', () => {
      it('should capitalize first letter', () => {
        expect(capitalize('hello')).toBe('Hello');
      });

      it('should handle empty string', () => {
        expect(capitalize('')).toBe('');
      });
    });

    describe('slugify', () => {
      it('should create slug from string', () => {
        expect(slugify('Hello World')).toBe('hello-world');
      });

      it('should handle special characters', () => {
        expect(slugify('Hello, World!')).toBe('hello-world');
      });

      it('should handle multiple spaces', () => {
        expect(slugify('Hello   World')).toBe('hello-world');
      });
    });
  });

  describe('debounce', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should debounce function calls', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn();
      debouncedFn();
      debouncedFn();

      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(100);

      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should pass arguments to debounced function', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn('arg1', 'arg2');

      vi.advanceTimersByTime(100);

      expect(fn).toHaveBeenCalledWith('arg1', 'arg2');
    });
  });

  describe('Validation utilities', () => {
    describe('isValidEmail', () => {
      it('should validate correct emails', () => {
        expect(isValidEmail('test@example.com')).toBe(true);
        expect(isValidEmail('user.name@domain.co')).toBe(true);
      });

      it('should reject invalid emails', () => {
        expect(isValidEmail('invalid')).toBe(false);
        expect(isValidEmail('invalid@')).toBe(false);
        expect(isValidEmail('@example.com')).toBe(false);
      });
    });

    describe('isValidUrl', () => {
      it('should validate correct URLs', () => {
        expect(isValidUrl('https://example.com')).toBe(true);
        expect(isValidUrl('http://localhost:3000')).toBe(true);
      });

      it('should reject invalid URLs', () => {
        expect(isValidUrl('not-a-url')).toBe(false);
        expect(isValidUrl('')).toBe(false);
      });
    });
  });

  describe('Permission checking', () => {
    const permissions = ['releases:view', 'releases:create', 'features:view'];

    describe('hasPermission', () => {
      it('should return true for matching permission', () => {
        expect(hasPermission(permissions, 'releases:view')).toBe(true);
      });

      it('should return false for missing permission', () => {
        expect(hasPermission(permissions, 'users:delete')).toBe(false);
      });

      it('should return true for wildcard permission', () => {
        expect(hasPermission(['*'], 'any:permission')).toBe(true);
      });
    });

    describe('hasAnyPermission', () => {
      it('should return true if any permission matches', () => {
        expect(hasAnyPermission(permissions, ['releases:view', 'users:delete'])).toBe(true);
      });

      it('should return false if no permissions match', () => {
        expect(hasAnyPermission(permissions, ['users:delete', 'admin:access'])).toBe(false);
      });
    });

    describe('hasAllPermissions', () => {
      it('should return true if all permissions match', () => {
        expect(hasAllPermissions(permissions, ['releases:view', 'features:view'])).toBe(true);
      });

      it('should return false if any permission is missing', () => {
        expect(hasAllPermissions(permissions, ['releases:view', 'users:delete'])).toBe(false);
      });
    });
  });

  describe('Sort and filter utilities', () => {
    const items = [
      { name: 'Charlie', age: 30 },
      { name: 'Alice', age: 25 },
      { name: 'Bob', age: 35 },
    ];

    describe('sortBy', () => {
      it('should sort by key ascending', () => {
        const sorted = sortBy(items, 'name', 'asc');
        expect(sorted[0].name).toBe('Alice');
        expect(sorted[1].name).toBe('Bob');
        expect(sorted[2].name).toBe('Charlie');
      });

      it('should sort by key descending', () => {
        const sorted = sortBy(items, 'age', 'desc');
        expect(sorted[0].age).toBe(35);
        expect(sorted[2].age).toBe(25);
      });

      it('should not mutate original array', () => {
        const originalFirst = items[0].name;
        sortBy(items, 'name', 'asc');
        expect(items[0].name).toBe(originalFirst);
      });
    });

    describe('filterBySearch', () => {
      it('should filter items by search term', () => {
        const filtered = filterBySearch(items, 'alice', ['name']);
        expect(filtered.length).toBe(1);
        expect(filtered[0].name).toBe('Alice');
      });

      it('should be case-insensitive', () => {
        const filtered = filterBySearch(items, 'ALICE', ['name']);
        expect(filtered.length).toBe(1);
      });

      it('should return all items for empty search', () => {
        const filtered = filterBySearch(items, '', ['name']);
        expect(filtered.length).toBe(3);
      });
    });
  });

  describe('localStorage utilities', () => {
    beforeEach(() => {
      localStorage.clear();
    });

    describe('getLocalStorage', () => {
      it('should return stored value', () => {
        localStorage.setItem('test', JSON.stringify({ foo: 'bar' }));
        const result = getLocalStorage('test', {});
        expect(result).toEqual({ foo: 'bar' });
      });

      it('should return default value for missing key', () => {
        const result = getLocalStorage('missing', 'default');
        expect(result).toBe('default');
      });
    });

    describe('setLocalStorage', () => {
      it('should store value', () => {
        setLocalStorage('test', { foo: 'bar' });
        const stored = localStorage.getItem('test');
        expect(JSON.parse(stored!)).toEqual({ foo: 'bar' });
      });
    });

    describe('removeLocalStorage', () => {
      it('should remove stored value', () => {
        localStorage.setItem('test', 'value');
        removeLocalStorage('test');
        expect(localStorage.getItem('test')).toBeNull();
      });
    });
  });
});

