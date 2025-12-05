/**
 * MSW Request Handlers
 * 
 * Mock API responses for testing purposes.
 * These handlers intercept API requests and return mock data.
 */

import { http, HttpResponse } from 'msw';

const API_URL = 'http://localhost:8088';

// ============================================================================
// MOCK DATA
// ============================================================================

export const mockUser = {
  id: 'user-1',
  email: 'admin@nexus.dev',
  name: 'Admin User',
  roles: ['admin'],
  permissions: ['*'],
  is_admin: true,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockDashboardStats = {
  total_releases: 12,
  active_agents: 5,
  pending_requests: 3,
  active_users: 10,
  system_health: 98,
  recent_activity: [
    {
      id: '1',
      type: 'release',
      title: 'Release v2.0.0 completed',
      description: 'Successfully deployed to production',
      timestamp: new Date().toISOString(),
      status: 'completed',
    },
    {
      id: '2',
      type: 'feature_request',
      title: 'New feature requested',
      description: 'User dashboard improvements',
      timestamp: new Date().toISOString(),
      status: 'pending',
    },
  ],
};

export const mockReleases = [
  {
    id: 'release-1',
    version: '2.0.0',
    name: 'Major Release',
    status: 'completed',
    release_date: '2024-01-15T00:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
    description: 'Major feature release',
    features: ['Feature 1', 'Feature 2'],
  },
  {
    id: 'release-2',
    version: '2.1.0',
    name: 'Minor Release',
    status: 'in_progress',
    release_date: '2024-02-01T00:00:00Z',
    created_at: '2024-01-20T00:00:00Z',
    updated_at: '2024-01-25T00:00:00Z',
    description: 'Minor improvements',
    features: ['Feature 3'],
  },
  {
    id: 'release-3',
    version: '3.0.0',
    name: 'Next Major',
    status: 'planned',
    release_date: '2024-06-01T00:00:00Z',
    created_at: '2024-01-25T00:00:00Z',
    updated_at: '2024-01-25T00:00:00Z',
    description: 'Next major release',
  },
];

export const mockHealthOverview = {
  overall_status: 'healthy',
  services: [
    {
      service: 'API Gateway',
      status: 'healthy',
      uptime: 99.9,
      uptime_percentage: 99.9,
      last_check: new Date().toISOString(),
      response_time: 45,
    },
    {
      service: 'Database',
      status: 'healthy',
      uptime: 99.99,
      uptime_percentage: 99.99,
      last_check: new Date().toISOString(),
      response_time: 12,
    },
    {
      service: 'Cache',
      status: 'degraded',
      uptime: 95.5,
      uptime_percentage: 95.5,
      last_check: new Date().toISOString(),
      response_time: 150,
      error_message: 'High latency detected',
    },
  ],
  total_services: 3,
  healthy_services: 2,
  last_updated: new Date().toISOString(),
};

export const mockFeatureRequests = [
  {
    id: 'fr-1',
    title: 'Dark mode support',
    description: 'Add dark mode theme to the dashboard',
    status: 'approved',
    priority: 'high',
    requested_by: 'user@example.com',
    created_at: '2024-01-10T00:00:00Z',
    updated_at: '2024-01-12T00:00:00Z',
    votes: 15,
  },
  {
    id: 'fr-2',
    title: 'Export to CSV',
    description: 'Ability to export data to CSV format',
    status: 'pending',
    priority: 'medium',
    requested_by: 'user2@example.com',
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
    votes: 8,
  },
];

export const mockConfig = {
  system_mode: 'production',
  sso_enabled: true,
  sso_provider: 'okta',
  jira_enabled: true,
  jira_url: 'https://jira.example.com',
  notifications_enabled: true,
};

export const mockUsers = [
  mockUser,
  {
    id: 'user-2',
    email: 'user@nexus.dev',
    name: 'Regular User',
    roles: ['user'],
    permissions: ['releases:view', 'features:view'],
    is_admin: false,
    is_active: true,
    created_at: '2024-01-05T00:00:00Z',
    updated_at: '2024-01-05T00:00:00Z',
  },
];

export const mockRoles = [
  {
    id: 'role-1',
    name: 'admin',
    description: 'Full system access',
    permissions: ['*'],
    is_system: true,
    user_count: 2,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'role-2',
    name: 'user',
    description: 'Basic user access',
    permissions: ['releases:view', 'features:view', 'features:create'],
    is_system: true,
    user_count: 5,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

// ============================================================================
// REQUEST HANDLERS
// ============================================================================

export const handlers = [
  // Auth endpoints
  http.post(`${API_URL}/auth/login`, () => {
    return HttpResponse.json({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      user: mockUser,
    });
  }),

  http.get(`${API_URL}/auth/me`, () => {
    return HttpResponse.json(mockUser);
  }),

  http.post(`${API_URL}/auth/logout`, () => {
    return HttpResponse.json({ success: true });
  }),

  http.get(`${API_URL}/auth/providers`, () => {
    return HttpResponse.json([
      { id: 'local', name: 'Local', enabled: true },
      { id: 'okta', name: 'Okta', enabled: true },
    ]);
  }),

  // Dashboard endpoints
  http.get(`${API_URL}/stats`, () => {
    return HttpResponse.json(mockDashboardStats);
  }),

  // Releases endpoints
  http.get(`${API_URL}/releases`, () => {
    return HttpResponse.json(mockReleases);
  }),

  http.get(`${API_URL}/releases/:id`, ({ params }) => {
    const release = mockReleases.find((r) => r.id === params.id);
    if (release) {
      return HttpResponse.json(release);
    }
    return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
  }),

  http.get(`${API_URL}/releases/calendar`, () => {
    return HttpResponse.json(mockReleases);
  }),

  // Health endpoints
  http.get(`${API_URL}/health`, () => {
    return HttpResponse.json(mockHealthOverview);
  }),

  http.get(`${API_URL}/health-check`, () => {
    return HttpResponse.json({
      status: 'healthy',
      service: 'admin-dashboard-backend',
      version: '2.4.0',
    });
  }),

  // Metrics endpoints
  http.get(`${API_URL}/metrics`, () => {
    return HttpResponse.json([
      { agent_name: 'Agent 1', requests_total: 1000, requests_success: 980 },
      { agent_name: 'Agent 2', requests_total: 500, requests_success: 495 },
    ]);
  }),

  http.get(`${API_URL}/api/metrics`, () => {
    return HttpResponse.text('# Prometheus metrics\n');
  }),

  // Feature requests endpoints
  http.get(`${API_URL}/feature-requests`, () => {
    return HttpResponse.json(mockFeatureRequests);
  }),

  http.get(`${API_URL}/feature-requests/:id`, ({ params }) => {
    const fr = mockFeatureRequests.find((f) => f.id === params.id);
    if (fr) {
      return HttpResponse.json(fr);
    }
    return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
  }),

  // Config endpoints
  http.get(`${API_URL}/config`, () => {
    return HttpResponse.json(mockConfig);
  }),

  http.get(`${API_URL}/config/templates`, () => {
    return HttpResponse.json([]);
  }),

  // RBAC endpoints
  http.get(`${API_URL}/users`, () => {
    return HttpResponse.json(mockUsers);
  }),

  http.get(`${API_URL}/users/:id`, ({ params }) => {
    const user = mockUsers.find((u) => u.id === params.id);
    if (user) {
      return HttpResponse.json(user);
    }
    return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
  }),

  http.get(`${API_URL}/roles`, () => {
    return HttpResponse.json(mockRoles);
  }),

  http.get(`${API_URL}/roles/permissions`, () => {
    return HttpResponse.json([
      { id: 'p1', name: 'releases:view', description: 'View releases' },
      { id: 'p2', name: 'releases:create', description: 'Create releases' },
      { id: 'p3', name: 'features:view', description: 'View feature requests' },
    ]);
  }),
];

