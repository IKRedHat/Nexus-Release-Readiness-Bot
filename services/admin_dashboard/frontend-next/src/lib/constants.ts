// ============================================================================
// NEXUS ADMIN DASHBOARD - CONSTANTS
// Application-wide constants and configuration
// ============================================================================

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://nexus-admin-api-63b4.onrender.com';

export const APP_VERSION = '3.0.0';
export const APP_NAME = 'Nexus Admin Dashboard';

// Routes
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  RELEASES: '/releases',
  METRICS: '/metrics',
  HEALTH: '/health',
  FEATURE_REQUESTS: '/feature-requests',
  SETTINGS: '/settings',
  ADMIN_USERS: '/admin/users',
  ADMIN_ROLES: '/admin/roles',
} as const;

// Permissions
export const PERMISSIONS = {
  // Users
  USERS_VIEW: 'users:view',
  USERS_CREATE: 'users:create',
  USERS_EDIT: 'users:edit',
  USERS_DELETE: 'users:delete',
  
  // Roles
  ROLES_VIEW: 'roles:view',
  ROLES_CREATE: 'roles:create',
  ROLES_EDIT: 'roles:edit',
  ROLES_DELETE: 'roles:delete',
  
  // Settings
  SETTINGS_VIEW: 'settings:view',
  SETTINGS_EDIT: 'settings:edit',
  
  // Releases
  RELEASES_VIEW: 'releases:view',
  RELEASES_CREATE: 'releases:create',
  RELEASES_EDIT: 'releases:edit',
  RELEASES_DELETE: 'releases:delete',
  
  // Metrics
  METRICS_VIEW: 'metrics:view',
  
  // Feature Requests
  FEATURES_VIEW: 'features:view',
  FEATURES_CREATE: 'features:create',
  FEATURES_APPROVE: 'features:approve',
} as const;

// Status options
export const RELEASE_STATUSES = [
  { value: 'planned', label: 'Planned' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
] as const;

export const FEATURE_STATUSES = [
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'implemented', label: 'Implemented' },
] as const;

export const PRIORITY_LEVELS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
] as const;

// Refresh intervals (milliseconds)
export const REFRESH_INTERVALS = {
  DASHBOARD: 30000,      // 30 seconds
  HEALTH: 10000,         // 10 seconds
  METRICS: 60000,        // 1 minute
  RELEASES: 120000,      // 2 minutes
  FEATURE_REQUESTS: 60000, // 1 minute
} as const;

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

// Chart colors
export const CHART_COLORS = {
  primary: '#00ff88',
  secondary: '#0ea5e9',
  success: '#22c55e',
  warning: '#fbbf24',
  danger: '#ef4444',
  info: '#3b82f6',
  purple: '#a855f7',
  cyan: '#06b6d4',
} as const;

// SSO Providers
export const SSO_PROVIDERS = [
  { id: 'okta', name: 'Okta', color: 'bg-blue-600' },
  { id: 'azure_ad', name: 'Microsoft Azure AD', color: 'bg-blue-500' },
  { id: 'google', name: 'Google', color: 'bg-red-500' },
  { id: 'github', name: 'GitHub', color: 'bg-gray-700' },
] as const;

