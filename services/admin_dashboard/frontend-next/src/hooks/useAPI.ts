'use client';

import useSWR, { SWRConfiguration } from 'swr';
import { api, endpoints } from '@/lib/api';
import type {
  DashboardStats,
  Release,
  HealthOverview,
  AgentMetrics,
  FeatureRequest,
  User,
  Role,
  Permission,
  Configuration,
} from '@/types';

// Generic API hook
export function useAPI<T>(endpoint: string | null, options?: SWRConfiguration) {
  const fetcher = (url: string) => api.get<T>(url);
  
  return useSWR<T>(endpoint, fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: true,
    ...options,
  });
}

// Dashboard
export function useDashboardStats(refreshInterval = 30000) {
  return useAPI<DashboardStats>(endpoints.dashboardStats, {
    refreshInterval,
    dedupingInterval: 5000,
  });
}

// Releases
export function useReleases() {
  return useAPI<Release[]>(endpoints.releases);
}

export function useRelease(id: string | null) {
  return useAPI<Release>(id ? `${endpoints.releases}/${id}` : null);
}

export function useReleaseCalendar() {
  return useAPI<any>(endpoints.releaseCalendar);
}

// Health
export function useHealthOverview(refreshInterval = 10000) {
  return useAPI<HealthOverview>(endpoints.healthOverview, {
    refreshInterval,
  });
}

export function useHealthStatus() {
  return useAPI<any>(endpoints.health, {
    refreshInterval: 10000,
  });
}

// Metrics
export function useMetrics() {
  return useAPI<AgentMetrics[]>(endpoints.metricsAggregated, {
    refreshInterval: 60000,
  });
}

export function useSystemMetrics() {
  return useAPI<any>('/metrics/system', {
    refreshInterval: 30000,
  });
}

// Feature Requests
export function useFeatureRequests(status?: string) {
  const url = status 
    ? `${endpoints.featureRequests}?status=${status}`
    : endpoints.featureRequests;
  
  return useAPI<FeatureRequest[]>(url);
}

export function useFeatureRequest(id: string | null) {
  return useAPI<FeatureRequest>(id ? `${endpoints.featureRequests}/${id}` : null);
}

// Configuration
export function useConfiguration() {
  return useAPI<Configuration>(endpoints.configuration);
}

export function useConfigTemplates() {
  return useAPI<any>(`${endpoints.configuration}/templates`);
}

// RBAC - Users
export function useUsers() {
  return useAPI<User[]>(endpoints.users);
}

export function useUser(id: string | null) {
  return useAPI<User>(id ? `${endpoints.users}/${id}` : null);
}

// RBAC - Roles
export function useRoles() {
  return useAPI<Role[]>(endpoints.roles);
}

export function useRole(id: string | null) {
  return useAPI<Role>(id ? `${endpoints.roles}/${id}` : null);
}

export function usePermissions() {
  return useAPI<Permission[]>(endpoints.permissions);
}

// Mutations helper
export async function mutateAPI<T>(
  endpoint: string,
  method: 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  data?: any
): Promise<T> {
  switch (method) {
    case 'POST':
      return api.post<T>(endpoint, data);
    case 'PUT':
      return api.put<T>(endpoint, data);
    case 'DELETE':
      return api.delete<T>(endpoint);
    case 'PATCH':
      return api.patch<T>(endpoint, data);
  }
}

