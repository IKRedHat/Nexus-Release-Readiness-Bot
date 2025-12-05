/**
 * MSW Request Handlers
 * 
 * Mock API responses for testing purposes.
 * These handlers intercept API requests and return realistic mock data.
 */

import { http, HttpResponse } from 'msw';

const API_URL = 'http://localhost:8088';

// ============================================================================
// MOCK DATA - Comprehensive Test Data
// ============================================================================

// ------------ USERS & AUTH ------------

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
  last_login: new Date().toISOString(),
  avatar_url: null,
};

export const mockUsers = [
  mockUser,
  {
    id: 'user-2',
    email: 'john.smith@nexus.dev',
    name: 'John Smith',
    roles: ['developer'],
    permissions: ['releases:view', 'releases:create', 'features:view', 'features:create'],
    is_admin: false,
    is_active: true,
    created_at: '2024-01-05T00:00:00Z',
    updated_at: '2024-02-15T00:00:00Z',
    last_login: '2024-03-01T10:30:00Z',
    avatar_url: null,
  },
  {
    id: 'user-3',
    email: 'jane.doe@nexus.dev',
    name: 'Jane Doe',
    roles: ['release_manager'],
    permissions: ['releases:*', 'features:view'],
    is_admin: false,
    is_active: true,
    created_at: '2024-01-10T00:00:00Z',
    updated_at: '2024-02-20T00:00:00Z',
    last_login: '2024-03-02T14:15:00Z',
    avatar_url: null,
  },
  {
    id: 'user-4',
    email: 'bob.wilson@nexus.dev',
    name: 'Bob Wilson',
    roles: ['viewer'],
    permissions: ['releases:view', 'features:view'],
    is_admin: false,
    is_active: false,
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-01-20T00:00:00Z',
    last_login: '2024-02-01T09:00:00Z',
    avatar_url: null,
  },
];

export const mockRoles = [
  {
    id: 'role-admin',
    name: 'admin',
    description: 'Full system access with all permissions',
    permissions: ['*'],
    is_system: true,
    user_count: 2,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'role-developer',
    name: 'developer',
    description: 'Access to create and manage releases and features',
    permissions: ['releases:view', 'releases:create', 'releases:edit', 'features:view', 'features:create'],
    is_system: true,
    user_count: 8,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'role-release-manager',
    name: 'release_manager',
    description: 'Full access to release management',
    permissions: ['releases:*', 'features:view', 'health:view'],
    is_system: true,
    user_count: 3,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'role-viewer',
    name: 'viewer',
    description: 'Read-only access to dashboard',
    permissions: ['releases:view', 'features:view', 'health:view', 'metrics:view'],
    is_system: true,
    user_count: 15,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'role-custom-qa',
    name: 'qa_engineer',
    description: 'Quality assurance team access',
    permissions: ['releases:view', 'releases:test', 'features:view', 'health:view'],
    is_system: false,
    user_count: 5,
    created_at: '2024-02-15T00:00:00Z',
    updated_at: '2024-02-20T00:00:00Z',
  },
];

export const mockPermissions = [
  { id: 'p1', name: 'releases:view', description: 'View releases', category: 'Releases' },
  { id: 'p2', name: 'releases:create', description: 'Create new releases', category: 'Releases' },
  { id: 'p3', name: 'releases:edit', description: 'Edit existing releases', category: 'Releases' },
  { id: 'p4', name: 'releases:delete', description: 'Delete releases', category: 'Releases' },
  { id: 'p5', name: 'releases:deploy', description: 'Deploy releases', category: 'Releases' },
  { id: 'p6', name: 'releases:test', description: 'Run release tests', category: 'Releases' },
  { id: 'p7', name: 'features:view', description: 'View feature requests', category: 'Features' },
  { id: 'p8', name: 'features:create', description: 'Create feature requests', category: 'Features' },
  { id: 'p9', name: 'features:approve', description: 'Approve feature requests', category: 'Features' },
  { id: 'p10', name: 'users:view', description: 'View users', category: 'Administration' },
  { id: 'p11', name: 'users:manage', description: 'Manage users', category: 'Administration' },
  { id: 'p12', name: 'roles:view', description: 'View roles', category: 'Administration' },
  { id: 'p13', name: 'roles:manage', description: 'Manage roles', category: 'Administration' },
  { id: 'p14', name: 'health:view', description: 'View system health', category: 'System' },
  { id: 'p15', name: 'metrics:view', description: 'View system metrics', category: 'System' },
  { id: 'p16', name: 'config:view', description: 'View configuration', category: 'System' },
  { id: 'p17', name: 'config:edit', description: 'Edit configuration', category: 'System' },
];

// ------------ DASHBOARD ------------

export const mockDashboardStats = {
  total_releases: 24,
  active_releases: 3,
  completed_releases: 18,
  active_agents: 8,
  pending_requests: 7,
  approved_requests: 12,
  active_users: 28,
  system_health: 98.5,
  uptime_percentage: 99.97,
  recent_activity: [
    {
      id: 'act-1',
      type: 'release',
      title: 'Release v2.4.0 deployed to production',
      description: 'Successfully deployed all components',
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      status: 'completed',
      user: 'jane.doe@nexus.dev',
    },
    {
      id: 'act-2',
      type: 'feature_request',
      title: 'Feature request approved: API Rate Limiting',
      description: 'Scheduled for v2.5.0',
      timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
      status: 'completed',
      user: 'admin@nexus.dev',
    },
    {
      id: 'act-3',
      type: 'release',
      title: 'Release v2.5.0 build started',
      description: 'CI/CD pipeline triggered',
      timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      status: 'in_progress',
      user: 'john.smith@nexus.dev',
    },
    {
      id: 'act-4',
      type: 'health',
      title: 'Cache service recovered',
      description: 'Redis cluster back to healthy state',
      timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
      status: 'completed',
      user: 'system',
    },
    {
      id: 'act-5',
      type: 'user',
      title: 'New user registered',
      description: 'alice.johnson@nexus.dev joined the platform',
      timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
      status: 'completed',
      user: 'system',
    },
    {
      id: 'act-6',
      type: 'config',
      title: 'SSO configuration updated',
      description: 'Added Azure AD provider',
      timestamp: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
      status: 'completed',
      user: 'admin@nexus.dev',
    },
  ],
};

// ------------ RELEASES ------------

export const mockReleases = [
  {
    id: 'release-1',
    version: '2.4.0',
    name: 'Performance Release',
    status: 'completed',
    release_type: 'minor',
    release_date: '2024-03-01T10:00:00Z',
    created_at: '2024-02-15T00:00:00Z',
    updated_at: '2024-03-01T10:00:00Z',
    description: 'Performance improvements and bug fixes',
    features: ['Optimized database queries', 'Reduced API latency', 'Fixed memory leak'],
    owner: 'jane.doe@nexus.dev',
    environment: 'production',
    deployment_status: 'deployed',
    test_coverage: 94.5,
    changelog: '## Changes\n- Improved query performance by 40%\n- Fixed critical memory leak\n- Updated dependencies',
  },
  {
    id: 'release-2',
    version: '2.5.0',
    name: 'Feature Release',
    status: 'in_progress',
    release_type: 'minor',
    release_date: '2024-03-15T10:00:00Z',
    created_at: '2024-03-01T00:00:00Z',
    updated_at: '2024-03-05T00:00:00Z',
    description: 'New features and enhancements',
    features: ['API Rate Limiting', 'Webhook support', 'Audit logging'],
    owner: 'john.smith@nexus.dev',
    environment: 'staging',
    deployment_status: 'pending',
    test_coverage: 88.2,
    changelog: '## Coming Soon\n- API rate limiting\n- Webhook integrations\n- Enhanced audit logging',
  },
  {
    id: 'release-3',
    version: '3.0.0',
    name: 'Major Platform Update',
    status: 'planned',
    release_type: 'major',
    release_date: '2024-06-01T10:00:00Z',
    created_at: '2024-02-01T00:00:00Z',
    updated_at: '2024-03-01T00:00:00Z',
    description: 'Major platform redesign with breaking changes',
    features: ['New UI/UX', 'GraphQL API', 'Multi-tenancy support'],
    owner: 'admin@nexus.dev',
    environment: 'development',
    deployment_status: 'not_started',
    test_coverage: 45.0,
    changelog: '## Planned\n- Complete UI redesign\n- GraphQL API alongside REST\n- Multi-tenant architecture',
  },
  {
    id: 'release-4',
    version: '2.4.1',
    name: 'Hotfix',
    status: 'in_progress',
    release_type: 'patch',
    release_date: '2024-03-08T14:00:00Z',
    created_at: '2024-03-05T00:00:00Z',
    updated_at: '2024-03-06T00:00:00Z',
    description: 'Critical security patch',
    features: ['Security fix for CVE-2024-1234'],
    owner: 'admin@nexus.dev',
    environment: 'staging',
    deployment_status: 'testing',
    test_coverage: 100,
    changelog: '## Security\n- Patched CVE-2024-1234',
  },
  {
    id: 'release-5',
    version: '2.3.0',
    name: 'Q4 Release',
    status: 'completed',
    release_type: 'minor',
    release_date: '2024-01-15T10:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    description: 'End of year feature release',
    features: ['Dark mode', 'Export functionality', 'Improved search'],
    owner: 'jane.doe@nexus.dev',
    environment: 'production',
    deployment_status: 'deployed',
    test_coverage: 92.1,
    changelog: '## Features\n- Dark mode support\n- CSV/PDF export\n- Enhanced search',
  },
];

// ------------ HEALTH ------------

export const mockHealthOverview = {
  overall_status: 'healthy',
  healthy_count: 5,
  degraded_count: 1,
  down_count: 0,
  total_services: 6,
  last_updated: new Date().toISOString(),
  services: [
    {
      service: 'API Gateway',
      status: 'healthy',
      uptime: 99.99,
      uptime_percentage: 99.99,
      last_check: new Date().toISOString(),
      response_time: 42,
      description: 'Main API entry point',
      endpoint: 'https://api.nexus.dev',
    },
    {
      service: 'PostgreSQL',
      status: 'healthy',
      uptime: 99.98,
      uptime_percentage: 99.98,
      last_check: new Date().toISOString(),
      response_time: 8,
      description: 'Primary database',
      endpoint: 'postgres://db.nexus.dev:5432',
    },
    {
      service: 'Redis Cache',
      status: 'degraded',
      uptime: 95.5,
      uptime_percentage: 95.5,
      last_check: new Date().toISOString(),
      response_time: 156,
      description: 'Distributed cache layer',
      endpoint: 'redis://cache.nexus.dev:6379',
      error_message: 'High latency detected - investigating',
    },
    {
      service: 'Message Queue',
      status: 'healthy',
      uptime: 99.95,
      uptime_percentage: 99.95,
      last_check: new Date().toISOString(),
      response_time: 15,
      description: 'RabbitMQ message broker',
      endpoint: 'amqp://mq.nexus.dev:5672',
    },
    {
      service: 'Search Service',
      status: 'healthy',
      uptime: 99.90,
      uptime_percentage: 99.90,
      last_check: new Date().toISOString(),
      response_time: 65,
      description: 'Elasticsearch cluster',
      endpoint: 'https://search.nexus.dev:9200',
    },
    {
      service: 'Storage Service',
      status: 'healthy',
      uptime: 99.999,
      uptime_percentage: 99.999,
      last_check: new Date().toISOString(),
      response_time: 125,
      description: 'S3-compatible object storage',
      endpoint: 's3://storage.nexus.dev',
    },
  ],
};

// ------------ METRICS ------------

export const mockMetrics = {
  system: {
    cpu_usage: 45.2,
    memory_usage: 68.5,
    memory_total: 32768,
    memory_used: 22446,
    disk_usage: 52.3,
    disk_total: 500,
    disk_used: 261.5,
    network_in: 1250000,
    network_out: 890000,
    load_average: [1.2, 1.5, 1.8],
  },
  agents: [
    {
      agent_name: 'Release Agent',
      agent_id: 'agent-release',
      status: 'active',
      requests_total: 15420,
      requests_success: 15210,
      requests_failed: 210,
      success_rate: 98.64,
      avg_response_time: 245,
      last_active: new Date(Date.now() - 1000 * 30).toISOString(),
    },
    {
      agent_name: 'Build Agent',
      agent_id: 'agent-build',
      status: 'active',
      requests_total: 8750,
      requests_success: 8642,
      requests_failed: 108,
      success_rate: 98.77,
      avg_response_time: 1850,
      last_active: new Date(Date.now() - 1000 * 15).toISOString(),
    },
    {
      agent_name: 'Test Agent',
      agent_id: 'agent-test',
      status: 'active',
      requests_total: 22100,
      requests_success: 21654,
      requests_failed: 446,
      success_rate: 97.98,
      avg_response_time: 3200,
      last_active: new Date(Date.now() - 1000 * 60).toISOString(),
    },
    {
      agent_name: 'Deploy Agent',
      agent_id: 'agent-deploy',
      status: 'idle',
      requests_total: 1250,
      requests_success: 1238,
      requests_failed: 12,
      success_rate: 99.04,
      avg_response_time: 45000,
      last_active: new Date(Date.now() - 1000 * 600).toISOString(),
    },
    {
      agent_name: 'Monitor Agent',
      agent_id: 'agent-monitor',
      status: 'active',
      requests_total: 125000,
      requests_success: 124875,
      requests_failed: 125,
      success_rate: 99.90,
      avg_response_time: 50,
      last_active: new Date().toISOString(),
    },
  ],
};

// ------------ FEATURE REQUESTS ------------

export const mockFeatureRequests = [
  {
    id: 'fr-1',
    title: 'API Rate Limiting',
    description: 'Implement configurable rate limiting for API endpoints to prevent abuse and ensure fair usage.',
    status: 'approved',
    priority: 'high',
    requested_by: 'john.smith@nexus.dev',
    assigned_to: 'jane.doe@nexus.dev',
    created_at: '2024-01-10T00:00:00Z',
    updated_at: '2024-02-15T00:00:00Z',
    target_release: '2.5.0',
    votes: 24,
    comments: 8,
    labels: ['security', 'api', 'performance'],
  },
  {
    id: 'fr-2',
    title: 'Export Dashboard Data',
    description: 'Ability to export dashboard metrics and reports to CSV, PDF, and Excel formats.',
    status: 'in_progress',
    priority: 'medium',
    requested_by: 'user2@nexus.dev',
    assigned_to: 'john.smith@nexus.dev',
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-03-01T00:00:00Z',
    target_release: '2.5.0',
    votes: 18,
    comments: 5,
    labels: ['ui', 'reporting'],
  },
  {
    id: 'fr-3',
    title: 'Webhook Notifications',
    description: 'Send webhook notifications for release events, build status changes, and system alerts.',
    status: 'pending',
    priority: 'high',
    requested_by: 'jane.doe@nexus.dev',
    assigned_to: null,
    created_at: '2024-02-01T00:00:00Z',
    updated_at: '2024-02-01T00:00:00Z',
    target_release: null,
    votes: 32,
    comments: 12,
    labels: ['integration', 'notifications'],
  },
  {
    id: 'fr-4',
    title: 'Multi-Environment Support',
    description: 'Support for managing releases across multiple environments (dev, staging, prod) with environment-specific configurations.',
    status: 'pending',
    priority: 'high',
    requested_by: 'admin@nexus.dev',
    assigned_to: null,
    created_at: '2024-02-10T00:00:00Z',
    updated_at: '2024-02-10T00:00:00Z',
    target_release: '3.0.0',
    votes: 45,
    comments: 15,
    labels: ['infrastructure', 'core'],
  },
  {
    id: 'fr-5',
    title: 'Slack Integration',
    description: 'Native Slack integration for notifications, release approvals, and status updates.',
    status: 'rejected',
    priority: 'low',
    requested_by: 'user3@nexus.dev',
    assigned_to: null,
    created_at: '2024-01-20T00:00:00Z',
    updated_at: '2024-02-05T00:00:00Z',
    target_release: null,
    votes: 5,
    comments: 3,
    labels: ['integration'],
    rejection_reason: 'Covered by webhook notifications feature',
  },
  {
    id: 'fr-6',
    title: 'Audit Log Export',
    description: 'Export audit logs for compliance and security review purposes.',
    status: 'approved',
    priority: 'medium',
    requested_by: 'jane.doe@nexus.dev',
    assigned_to: 'john.smith@nexus.dev',
    created_at: '2024-02-20T00:00:00Z',
    updated_at: '2024-03-01T00:00:00Z',
    target_release: '2.6.0',
    votes: 12,
    comments: 4,
    labels: ['security', 'compliance'],
  },
  {
    id: 'fr-7',
    title: 'Custom Dashboard Widgets',
    description: 'Allow users to create and arrange custom widgets on their dashboard.',
    status: 'pending',
    priority: 'low',
    requested_by: 'user4@nexus.dev',
    assigned_to: null,
    created_at: '2024-03-01T00:00:00Z',
    updated_at: '2024-03-01T00:00:00Z',
    target_release: null,
    votes: 8,
    comments: 2,
    labels: ['ui', 'customization'],
  },
];

// ------------ CONFIGURATION ------------

export const mockConfig = {
  system: {
    system_mode: 'production',
    debug_mode: false,
    maintenance_mode: false,
    max_concurrent_builds: 5,
    build_timeout_minutes: 30,
    log_retention_days: 90,
  },
  sso: {
    enabled: true,
    providers: [
      { id: 'okta', name: 'Okta', enabled: true, configured: true },
      { id: 'azure', name: 'Azure AD', enabled: true, configured: true },
      { id: 'google', name: 'Google', enabled: false, configured: false },
      { id: 'github', name: 'GitHub', enabled: true, configured: true },
    ],
    default_provider: 'okta',
    allow_local_login: true,
  },
  jira: {
    enabled: true,
    url: 'https://nexus.atlassian.net',
    project_key: 'NEX',
    sync_enabled: true,
    sync_interval_minutes: 15,
  },
  notifications: {
    enabled: true,
    email_enabled: true,
    slack_enabled: false,
    webhook_enabled: true,
    default_channels: ['releases', 'alerts'],
  },
  api: {
    rate_limit_enabled: true,
    rate_limit_requests: 1000,
    rate_limit_window_seconds: 60,
    cors_origins: ['https://nexus.dev', 'https://admin.nexus.dev'],
    api_key_expiry_days: 365,
  },
};

// ============================================================================
// REQUEST HANDLERS
// ============================================================================

export const handlers = [
  // ------------ AUTH ENDPOINTS ------------
  
  http.post(`${API_URL}/auth/login`, async ({ request }) => {
    const body = await request.json() as { email?: string; password?: string };
    
    // Simulate invalid credentials
    if (body.email !== 'admin@nexus.dev' && body.password !== 'nexus') {
      return HttpResponse.json(
        { detail: 'Invalid email or password' },
        { status: 401 }
      );
    }
    
    return HttpResponse.json({
      access_token: 'mock-access-token-' + Date.now(),
      refresh_token: 'mock-refresh-token-' + Date.now(),
      token_type: 'Bearer',
      expires_in: 3600,
      user: mockUser,
    });
  }),

  http.get(`${API_URL}/auth/me`, () => {
    return HttpResponse.json(mockUser);
  }),

  http.post(`${API_URL}/auth/logout`, () => {
    return HttpResponse.json({ success: true, message: 'Logged out successfully' });
  }),

  http.post(`${API_URL}/auth/refresh`, () => {
    return HttpResponse.json({
      access_token: 'mock-access-token-refreshed-' + Date.now(),
      token_type: 'Bearer',
      expires_in: 3600,
    });
  }),

  http.get(`${API_URL}/auth/providers`, () => {
    return HttpResponse.json([
      { id: 'local', name: 'Local', enabled: true, icon: 'key' },
      { id: 'okta', name: 'Okta', enabled: true, icon: 'okta' },
      { id: 'azure', name: 'Azure AD', enabled: true, icon: 'microsoft' },
      { id: 'github', name: 'GitHub', enabled: true, icon: 'github' },
    ]);
  }),

  // ------------ DASHBOARD ENDPOINTS ------------

  http.get(`${API_URL}/stats`, () => {
    return HttpResponse.json(mockDashboardStats);
  }),

  // ------------ RELEASES ENDPOINTS ------------

  http.get(`${API_URL}/releases`, () => {
    return HttpResponse.json(mockReleases);
  }),

  http.get(`${API_URL}/releases/:id`, ({ params }) => {
    const release = mockReleases.find((r) => r.id === params.id);
    if (release) {
      return HttpResponse.json(release);
    }
    return HttpResponse.json({ detail: 'Release not found' }, { status: 404 });
  }),

  http.post(`${API_URL}/releases`, async ({ request }) => {
    const body = await request.json();
    const newRelease = {
      id: 'release-' + Date.now(),
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return HttpResponse.json(newRelease, { status: 201 });
  }),

  http.put(`${API_URL}/releases/:id`, async ({ params, request }) => {
    const body = await request.json();
    const release = mockReleases.find((r) => r.id === params.id);
    if (release) {
      return HttpResponse.json({ ...release, ...body, updated_at: new Date().toISOString() });
    }
    return HttpResponse.json({ detail: 'Release not found' }, { status: 404 });
  }),

  http.delete(`${API_URL}/releases/:id`, ({ params }) => {
    const release = mockReleases.find((r) => r.id === params.id);
    if (release) {
      return HttpResponse.json({ success: true, message: 'Release deleted' });
    }
    return HttpResponse.json({ detail: 'Release not found' }, { status: 404 });
  }),

  http.get(`${API_URL}/releases/calendar`, () => {
    return HttpResponse.json(mockReleases.map(r => ({
      id: r.id,
      title: `${r.version} - ${r.name}`,
      date: r.release_date,
      status: r.status,
    })));
  }),

  // ------------ HEALTH ENDPOINTS ------------

  http.get(`${API_URL}/health`, () => {
    return HttpResponse.json(mockHealthOverview);
  }),

  http.get(`${API_URL}/health-check`, () => {
    return HttpResponse.json({
      status: 'healthy',
      service: 'nexus-admin-backend',
      version: '2.4.0',
      timestamp: new Date().toISOString(),
    });
  }),

  // ------------ METRICS ENDPOINTS ------------

  http.get(`${API_URL}/metrics`, () => {
    return HttpResponse.json(mockMetrics.agents);
  }),

  http.get(`${API_URL}/api/metrics`, () => {
    return HttpResponse.text(`# HELP nexus_requests_total Total requests
# TYPE nexus_requests_total counter
nexus_requests_total{agent="release"} 15420
nexus_requests_total{agent="build"} 8750
nexus_requests_total{agent="test"} 22100

# HELP nexus_cpu_usage_percent CPU usage percentage
# TYPE nexus_cpu_usage_percent gauge
nexus_cpu_usage_percent 45.2

# HELP nexus_memory_usage_bytes Memory usage in bytes
# TYPE nexus_memory_usage_bytes gauge
nexus_memory_usage_bytes 22446000000
`);
  }),

  http.get(`${API_URL}/metrics/system`, () => {
    return HttpResponse.json(mockMetrics.system);
  }),

  // ------------ FEATURE REQUESTS ENDPOINTS ------------

  http.get(`${API_URL}/feature-requests`, ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    
    let filtered = mockFeatureRequests;
    if (status && status !== 'all') {
      filtered = mockFeatureRequests.filter(fr => fr.status === status);
    }
    
    return HttpResponse.json(filtered);
  }),

  http.get(`${API_URL}/feature-requests/:id`, ({ params }) => {
    const fr = mockFeatureRequests.find((f) => f.id === params.id);
    if (fr) {
      return HttpResponse.json(fr);
    }
    return HttpResponse.json({ detail: 'Feature request not found' }, { status: 404 });
  }),

  http.post(`${API_URL}/feature-requests`, async ({ request }) => {
    const body = await request.json();
    const newFr = {
      id: 'fr-' + Date.now(),
      ...body,
      status: 'pending',
      votes: 0,
      comments: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return HttpResponse.json(newFr, { status: 201 });
  }),

  http.post(`${API_URL}/feature-requests/:id/vote`, ({ params }) => {
    const fr = mockFeatureRequests.find((f) => f.id === params.id);
    if (fr) {
      return HttpResponse.json({ ...fr, votes: fr.votes + 1 });
    }
    return HttpResponse.json({ detail: 'Feature request not found' }, { status: 404 });
  }),

  // ------------ CONFIG ENDPOINTS ------------

  http.get(`${API_URL}/config`, () => {
    return HttpResponse.json(mockConfig);
  }),

  http.put(`${API_URL}/config`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ ...mockConfig, ...body });
  }),

  http.get(`${API_URL}/config/templates`, () => {
    return HttpResponse.json([
      { id: 't1', name: 'Production', description: 'Production environment defaults' },
      { id: 't2', name: 'Staging', description: 'Staging environment defaults' },
      { id: 't3', name: 'Development', description: 'Development environment defaults' },
    ]);
  }),

  // ------------ RBAC ENDPOINTS ------------

  http.get(`${API_URL}/users`, () => {
    return HttpResponse.json(mockUsers);
  }),

  http.get(`${API_URL}/users/:id`, ({ params }) => {
    const user = mockUsers.find((u) => u.id === params.id);
    if (user) {
      return HttpResponse.json(user);
    }
    return HttpResponse.json({ detail: 'User not found' }, { status: 404 });
  }),

  http.post(`${API_URL}/users`, async ({ request }) => {
    const body = await request.json();
    const newUser = {
      id: 'user-' + Date.now(),
      ...body,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return HttpResponse.json(newUser, { status: 201 });
  }),

  http.put(`${API_URL}/users/:id`, async ({ params, request }) => {
    const body = await request.json();
    const user = mockUsers.find((u) => u.id === params.id);
    if (user) {
      return HttpResponse.json({ ...user, ...body, updated_at: new Date().toISOString() });
    }
    return HttpResponse.json({ detail: 'User not found' }, { status: 404 });
  }),

  http.delete(`${API_URL}/users/:id`, ({ params }) => {
    const user = mockUsers.find((u) => u.id === params.id);
    if (user) {
      return HttpResponse.json({ success: true, message: 'User deleted' });
    }
    return HttpResponse.json({ detail: 'User not found' }, { status: 404 });
  }),

  http.get(`${API_URL}/roles`, () => {
    return HttpResponse.json(mockRoles);
  }),

  http.get(`${API_URL}/roles/:id`, ({ params }) => {
    const role = mockRoles.find((r) => r.id === params.id);
    if (role) {
      return HttpResponse.json(role);
    }
    return HttpResponse.json({ detail: 'Role not found' }, { status: 404 });
  }),

  http.post(`${API_URL}/roles`, async ({ request }) => {
    const body = await request.json();
    const newRole = {
      id: 'role-' + Date.now(),
      ...body,
      is_system: false,
      user_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return HttpResponse.json(newRole, { status: 201 });
  }),

  http.get(`${API_URL}/roles/permissions`, () => {
    return HttpResponse.json(mockPermissions);
  }),
];
