import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://nexus-admin-api-63b4.onrender.com';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use((config) => {
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('nexus_access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }
      return config;
    });

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired
          if (typeof window !== 'undefined') {
            localStorage.removeItem('nexus_access_token');
            localStorage.removeItem('nexus_refresh_token');
            localStorage.removeItem('nexus_user');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }
}

export const api = new ApiClient();

// Endpoints
export const endpoints = {
  // Auth
  login: '/auth/login',
  logout: '/auth/logout',
  me: '/auth/me',
  providers: '/auth/providers',
  
  // Dashboard
  dashboardStats: '/dashboard/stats',
  
  // Releases
  releases: '/releases',
  releaseCalendar: '/releases/calendar',
  
  // Health
  health: '/health',
  healthOverview: '/health/overview',
  
  // Metrics
  metrics: '/metrics',
  metricsAggregated: '/metrics/aggregated',
  
  // Feature Requests
  featureRequests: '/feature-requests',
  
  // Settings
  configuration: '/configuration',
  
  // RBAC
  users: '/rbac/users',
  roles: '/rbac/roles',
  permissions: '/rbac/permissions',
};

