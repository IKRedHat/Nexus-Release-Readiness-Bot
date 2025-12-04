// ============================================================================
// NEXUS ADMIN DASHBOARD - TYPESCRIPT TYPES
// Complete type definitions for all features
// ============================================================================

export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
  permissions: string[];
  is_admin: boolean;
  avatar_url?: string;
  sso_provider?: string;
  sso_id?: string;
  created_at: string;
  updated_at: string;
  last_login?: string;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface DashboardStats {
  total_releases: number;
  active_agents: number;
  pending_requests: number;
  active_users: number;
  system_health: number;
  recent_activity: Activity[];
}

export interface Activity {
  id: string;
  type: 'release' | 'feature_request' | 'user' | 'role' | 'config' | 'system';
  title: string;
  description: string;
  timestamp: string;
  user?: string;
  status?: string;
  icon?: string;
}

export interface Release {
  id: string;
  version: string;
  name: string;
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled';
  release_date: string;
  created_at: string;
  updated_at: string;
  description?: string;
  features?: string[];
  bugs_fixed?: string[];
  risk_level?: 'low' | 'medium' | 'high';
  owner?: string;
}

export interface HealthService {
  service: string;
  status: 'healthy' | 'degraded' | 'down';
  uptime: number;
  uptime_percentage: number;
  last_check: string;
  response_time?: number;
  error_message?: string;
  port?: number;
  dependencies?: string[];
}

export interface HealthOverview {
  overall_status: 'healthy' | 'degraded' | 'down';
  services: HealthService[];
  total_services: number;
  healthy_services: number;
  last_updated: string;
}

export interface MetricData {
  timestamp: string;
  value: number;
  label?: string;
}

export interface AgentMetrics {
  agent_name: string;
  requests_total: number;
  requests_success: number;
  requests_failed: number;
  avg_response_time: number;
  uptime: number;
  last_activity: string;
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_in: number;
  network_out: number;
  active_connections: number;
}

export interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'approved' | 'rejected' | 'implemented' | 'in_progress';
  priority: 'low' | 'medium' | 'high' | 'critical';
  requested_by: string;
  assigned_to?: string;
  created_at: string;
  updated_at: string;
  jira_ticket?: string;
  jira_status?: string;
  votes: number;
  comments?: Comment[];
  labels?: string[];
}

export interface Comment {
  id: string;
  user: string;
  content: string;
  created_at: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  is_system: boolean;
  user_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
  scope?: string;
}

export interface Configuration {
  [key: string]: any;
  system_mode?: 'development' | 'staging' | 'production';
  sso_enabled?: boolean;
  sso_provider?: string;
  jira_enabled?: boolean;
  jira_url?: string;
  notifications_enabled?: boolean;
  auto_create_jira?: boolean;
}

export interface ApiError {
  detail: string;
  status_code: number;
  field?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  success: boolean;
  message?: string;
}

export interface FilterOptions {
  status?: string[];
  priority?: string[];
  dateFrom?: string;
  dateTo?: string;
  search?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface ChartDataPoint {
  name: string;
  value: number;
  timestamp?: string;
  [key: string]: any;
}

