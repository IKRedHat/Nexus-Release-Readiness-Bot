/**
 * API Client for Nexus Admin Dashboard
 * 
 * Features:
 * - Automatic token management
 * - Token refresh on 401
 * - Retry logic with exponential backoff
 * - Request/response interceptors
 * - Type-safe API calls
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://nexus-admin-api-63b4.onrender.com';

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY_BASE = 1000; // 1 second
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504];

// Token storage keys
const TOKEN_KEY = 'nexus_access_token';
const REFRESH_TOKEN_KEY = 'nexus_refresh_token';
const USER_KEY = 'nexus_user';

/**
 * Sleep helper for retry delays
 */
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Calculate exponential backoff delay
 */
const getRetryDelay = (attempt: number): number => {
  return Math.min(RETRY_DELAY_BASE * Math.pow(2, attempt), 30000); // Max 30 seconds
};

/**
 * Check if error is retryable
 */
const isRetryableError = (error: AxiosError): boolean => {
  // Network errors are retryable
  if (!error.response) return true;
  
  // Specific status codes are retryable
  return RETRYABLE_STATUS_CODES.includes(error.response.status);
};

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private refreshSubscribers: ((token: string) => void)[] = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem(TOKEN_KEY);
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean; _retryCount?: number };
        
        // Handle 401 - Token expired
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          if (this.isRefreshing) {
            // Wait for the refresh to complete
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                originalRequest.headers = originalRequest.headers || {};
                originalRequest.headers.Authorization = `Bearer ${token}`;
                resolve(this.client(originalRequest));
              });
            });
          }
          
          this.isRefreshing = true;
          
          try {
            const newToken = await this.refreshToken();
            
            if (newToken) {
              // Notify all waiting requests
              this.refreshSubscribers.forEach((callback) => callback(newToken));
              this.refreshSubscribers = [];
              
              // Retry original request
              originalRequest.headers = originalRequest.headers || {};
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, logout user
            this.handleLogout();
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  /**
   * Attempt to refresh the access token
   */
  private async refreshToken(): Promise<string | null> {
    if (typeof window === 'undefined') return null;
    
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      this.handleLogout();
      return null;
    }
    
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      });
      
      const { access_token, refresh_token: newRefreshToken } = response.data;
      
      localStorage.setItem(TOKEN_KEY, access_token);
      if (newRefreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken);
      }
      
      return access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.handleLogout();
      return null;
    }
  }

  /**
   * Handle logout - clear tokens and redirect
   */
  private handleLogout() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      
      // Only redirect if not already on login page
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
  }

  /**
   * Make request with retry logic
   */
  private async requestWithRetry<T>(
    requestFn: () => Promise<T>,
    retryCount = 0
  ): Promise<T> {
    try {
      return await requestFn();
    } catch (error) {
      const axiosError = error as AxiosError;
      
      if (retryCount < MAX_RETRIES && isRetryableError(axiosError)) {
        const delay = getRetryDelay(retryCount);
        console.warn(`Request failed, retrying in ${delay}ms... (attempt ${retryCount + 1}/${MAX_RETRIES})`);
        
        await sleep(delay);
        return this.requestWithRetry(requestFn, retryCount + 1);
      }
      
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.requestWithRetry(async () => {
      const response = await this.client.get<T>(url, config);
      return response.data;
    });
  }

  /**
   * POST request
   */
  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.requestWithRetry(async () => {
      const response = await this.client.post<T>(url, data, config);
      return response.data;
    });
  }

  /**
   * PUT request
   */
  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.requestWithRetry(async () => {
      const response = await this.client.put<T>(url, data, config);
      return response.data;
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.requestWithRetry(async () => {
      const response = await this.client.delete<T>(url, config);
      return response.data;
    });
  }

  /**
   * PATCH request
   */
  async patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.requestWithRetry(async () => {
      const response = await this.client.patch<T>(url, data, config);
      return response.data;
    });
  }

  /**
   * Get the base URL
   */
  getBaseUrl(): string {
    return API_BASE_URL;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem(TOKEN_KEY);
  }
}

export const api = new ApiClient();

// API Endpoints
export const endpoints = {
  // Auth
  login: '/auth/login',
  logout: '/auth/logout',
  me: '/auth/me',
  refresh: '/auth/refresh',
  providers: '/auth/providers',
  
  // Dashboard
  dashboardStats: '/stats',
  
  // Releases
  releases: '/releases',
  releaseCalendar: '/releases/calendar',
  
  // Health
  health: '/health-check',
  healthOverview: '/health',
  
  // Metrics
  metrics: '/api/metrics',
  metricsAggregated: '/metrics',
  
  // Feature Requests
  featureRequests: '/feature-requests',
  
  // Settings/Configuration
  configuration: '/config',
  configTemplates: '/config/templates',
  
  // System Mode
  mode: '/mode',
  
  // RBAC
  users: '/users',
  roles: '/roles',
  permissions: '/roles/permissions',
};

// Re-export types for convenience
export type { AxiosRequestConfig, AxiosError };
