import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistance, formatRelative } from 'date-fns';

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Date formatting utilities
export function formatDate(date: string | Date, formatStr: string = 'MMM d, yyyy'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return format(d, formatStr);
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return formatDistance(d, new Date(), { addSuffix: true });
}

export function formatDateTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return format(d, 'MMM d, yyyy HH:mm:ss');
}

// Status utilities
export function getStatusColor(status: string): string {
  const statusMap: Record<string, string> = {
    // Health statuses
    healthy: 'text-green-500 bg-green-500/10 border-green-500/20',
    degraded: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20',
    down: 'text-red-500 bg-red-500/10 border-red-500/20',
    
    // Release statuses
    completed: 'text-green-500 bg-green-500/10 border-green-500/20',
    in_progress: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
    planned: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
    pending: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20',
    cancelled: 'text-gray-500 bg-gray-500/10 border-gray-500/20',
    
    // Feature request statuses
    approved: 'text-green-500 bg-green-500/10 border-green-500/20',
    rejected: 'text-red-500 bg-red-500/10 border-red-500/20',
    implemented: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
    
    // Priority levels
    low: 'text-gray-500 bg-gray-500/10 border-gray-500/20',
    medium: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
    high: 'text-orange-500 bg-orange-500/10 border-orange-500/20',
    critical: 'text-red-500 bg-red-500/10 border-red-500/20',
  };
  
  return statusMap[status.toLowerCase()] || 'text-gray-500 bg-gray-500/10 border-gray-500/20';
}

export function getStatusIcon(status: string): string {
  const iconMap: Record<string, string> = {
    healthy: '●',
    degraded: '◐',
    down: '○',
    completed: '✓',
    in_progress: '↻',
    pending: '○',
    cancelled: '✕',
  };
  
  return iconMap[status.toLowerCase()] || '○';
}

// Number formatting
export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

export function formatPercentage(num: number, decimals: number = 1): string {
  return `${num.toFixed(decimals)}%`;
}

export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

// String utilities
export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return `${str.slice(0, length)}...`;
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function slugify(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// Debounce function
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

// Validation utilities
export function isValidEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

// Permission checking
export function hasPermission(userPermissions: string[], required: string): boolean {
  return userPermissions.includes(required) || userPermissions.includes('*');
}

export function hasAnyPermission(userPermissions: string[], required: string[]): boolean {
  return required.some(perm => hasPermission(userPermissions, perm));
}

export function hasAllPermissions(userPermissions: string[], required: string[]): boolean {
  return required.every(perm => hasPermission(userPermissions, perm));
}

// Sort utilities
export function sortBy<T>(array: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): T[] {
  return [...array].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];
    
    if (aVal < bVal) return order === 'asc' ? -1 : 1;
    if (aVal > bVal) return order === 'asc' ? 1 : -1;
    return 0;
  });
}

// Filter utilities
export function filterBySearch<T>(
  items: T[],
  searchTerm: string,
  fields: (keyof T)[]
): T[] {
  if (!searchTerm) return items;
  
  const term = searchTerm.toLowerCase();
  return items.filter(item =>
    fields.some(field => {
      const value = item[field];
      return value && String(value).toLowerCase().includes(term);
    })
  );
}

// Local storage utilities (safe for SSR)
export function getLocalStorage<T>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') return defaultValue;
  
  try {
    const item = window.localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch {
    return defaultValue;
  }
}

export function setLocalStorage<T>(key: string, value: T): void {
  if (typeof window === 'undefined') return;
  
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('Error saving to localStorage:', error);
  }
}

export function removeLocalStorage(key: string): void {
  if (typeof window === 'undefined') return;
  
  try {
    window.localStorage.removeItem(key);
  } catch (error) {
    console.error('Error removing from localStorage:', error);
  }
}

