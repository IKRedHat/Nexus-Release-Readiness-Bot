#!/bin/bash
set -e

echo "🚀 Nexus Admin Dashboard - Next.js 14 Code Generation"
echo "===================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="$(pwd)"

echo -e "${BLUE}📁 Creating directory structure...${NC}"

# Create all directories
mkdir -p src/{app/{api/proxy,login,releases,metrics,health,feature-requests,settings,admin/{users,roles}},components/{ui,layout,auth,dashboard,releases,metrics,health,feature-requests,settings,admin},lib,hooks,providers,types,styles}
mkdir -p public

echo -e "${GREEN}✓ Directory structure created${NC}"

# =============================================================================
# PACKAGE.JSON (already created, but ensure tailwindcss-animate)
# =============================================================================
echo -e "${BLUE}📦 Updating package.json with missing dependencies...${NC}"

cat > package.json << 'EOF'
{
  "name": "nexus-admin-dashboard",
  "version": "3.0.0",
  "private": true,
  "type": "module",
  "engines": {
    "node": "20.x"
  },
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.2.15",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "axios": "^1.7.7",
    "date-fns": "^3.6.0",
    "recharts": "^2.12.7",
    "lucide-react": "^0.447.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.3",
    "class-variance-authority": "^0.7.0",
    "swr": "^2.2.5"
  },
  "devDependencies": {
    "@types/node": "^22.8.6",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "typescript": "^5.6.3",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "tailwindcss-animate": "^1.0.7",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.13.0",
    "eslint-config-next": "14.2.15"
  }
}
EOF

echo -e "${GREEN}✓ package.json updated${NC}"

# =============================================================================
# GLOBAL STYLES
# =============================================================================
echo -e "${BLUE}🎨 Creating global styles...${NC}"

cat > src/styles/globals.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 160 84% 39%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 217.2 91.2% 59.8%;
    --radius: 0.5rem;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}

@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: hsl(var(--muted));
}

::-webkit-scrollbar-thumb {
  background: hsl(var(--primary) / 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--primary) / 0.5);
}

/* Animations */
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}
EOF

echo -e "${GREEN}✓ Global styles created${NC}"

# =============================================================================
# TYPES
# =============================================================================
echo -e "${BLUE}📝 Creating TypeScript types...${NC}"

cat > src/types/index.ts << 'EOF'
export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
  permissions: string[];
  is_admin: boolean;
  avatar_url?: string;
  sso_provider?: string;
  created_at?: string;
  last_login?: string;
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
  system_health: number;
  recent_activity: Activity[];
}

export interface Activity {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  user?: string;
  status?: string;
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
}

export interface HealthStatus {
  service: string;
  status: 'healthy' | 'degraded' | 'down';
  uptime: number;
  last_check: string;
  response_time?: number;
  error_message?: string;
}

export interface MetricData {
  timestamp: string;
  value: number;
  label?: string;
}

export interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'approved' | 'rejected' | 'implemented';
  priority: 'low' | 'medium' | 'high' | 'critical';
  requested_by: string;
  created_at: string;
  updated_at: string;
  jira_ticket?: string;
  votes?: number;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  is_system: boolean;
  user_count?: number;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
EOF

echo -e "${GREEN}✓ Types created${NC}"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
echo -e "${BLUE}🔧 Creating utility functions...${NC}"

cat > src/lib/utils.ts << 'EOF'
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date, format: 'short' | 'long' | 'relative' = 'short'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  if (format === 'relative') {
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  }
  
  if (format === 'long') {
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
  
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function getStatusColor(status: string): string {
  const statusMap: Record<string, string> = {
    healthy: 'text-green-400 bg-green-400/10',
    degraded: 'text-yellow-400 bg-yellow-400/10',
    down: 'text-red-400 bg-red-400/10',
    completed: 'text-green-400 bg-green-400/10',
    in_progress: 'text-blue-400 bg-blue-400/10',
    pending: 'text-yellow-400 bg-yellow-400/10',
    cancelled: 'text-gray-400 bg-gray-400/10',
    approved: 'text-green-400 bg-green-400/10',
    rejected: 'text-red-400 bg-red-400/10',
    implemented: 'text-purple-400 bg-purple-400/10',
  };
  
  return statusMap[status.toLowerCase()] || 'text-gray-400 bg-gray-400/10';
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}

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
EOF

cat > src/lib/constants.ts << 'EOF'
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://nexus-admin-api-63b4.onrender.com';

export const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION || '3.0.0';

export const PERMISSIONS = {
  USERS_VIEW: 'users:view',
  USERS_CREATE: 'users:create',
  USERS_EDIT: 'users:edit',
  USERS_DELETE: 'users:delete',
  ROLES_VIEW: 'roles:view',
  ROLES_CREATE: 'roles:create',
  ROLES_EDIT: 'roles:edit',
  ROLES_DELETE: 'roles:delete',
  SETTINGS_VIEW: 'settings:view',
  SETTINGS_EDIT: 'settings:edit',
  RELEASES_VIEW: 'releases:view',
  RELEASES_MANAGE: 'releases:manage',
  METRICS_VIEW: 'metrics:view',
} as const;

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
EOF

echo -e "${GREEN}✓ Utility functions created${NC}"

# =============================================================================
# API CLIENT
# =============================================================================
echo -e "${BLUE}🌐 Creating API client...${NC}"

cat > src/lib/api.ts << 'EOF'
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { API_BASE_URL } from './constants';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
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
          // Token expired, try to refresh
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

// API endpoints
export const endpoints = {
  // Auth
  login: '/auth/login',
  logout: '/auth/logout',
  me: '/auth/me',
  ssoProviders: '/auth/providers',
  ssoLogin: (provider: string) => `/auth/sso/${provider}`,
  
  // Dashboard
  dashboardStats: '/dashboard/stats',
  
  // Releases
  releases: '/releases',
  releaseById: (id: string) => `/releases/${id}`,
  releaseCalendar: '/releases/calendar',
  
  // Health
  health: '/health',
  healthOverview: '/health/overview',
  
  // Metrics
  metrics: '/metrics',
  metricsAggregated: '/metrics/aggregated',
  
  // Feature Requests
  featureRequests: '/feature-requests',
  featureRequestById: (id: string) => `/feature-requests/${id}`,
  featureRequestVote: (id: string) => `/feature-requests/${id}/vote`,
  
  // Settings
  configuration: '/configuration',
  configTemplates: '/configuration/templates',
  
  // Users
  users: '/rbac/users',
  userById: (id: string) => `/rbac/users/${id}`,
  
  // Roles
  roles: '/rbac/roles',
  roleById: (id: string) => `/rbac/roles/${id}`,
  permissions: '/rbac/permissions',
};
EOF

echo -e "${GREEN}✓ API client created${NC}"

echo ""
echo -e "${YELLOW}⏱️  This will take a moment...${NC}"
echo ""

# Continue with remaining files...
# Due to length, I'll create the script in parts. Let me continue...

# =============================================================================
# UI COMPONENTS - Part 1
# =============================================================================
echo -e "${BLUE}🎨 Creating UI components (Button)...${NC}"

cat > src/components/ui/button.tsx << 'EOF'
import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
EOF

echo -e "${GREEN}✓ Button component created${NC}"

echo -e "${BLUE}🎨 Creating UI components (Card)...${NC}"

cat > src/components/ui/card.tsx << 'EOF'
import * as React from 'react';
import { cn } from '@/lib/utils';

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'rounded-lg border bg-card text-card-foreground shadow-sm',
      className
    )}
    {...props}
  />
));
Card.displayName = 'Card';

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 p-6', className)}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      'text-2xl font-semibold leading-none tracking-tight',
      className
    )}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-muted-foreground', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
));
CardContent.displayName = 'CardContent';

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center p-6 pt-0', className)}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
EOF

echo -e "${GREEN}✓ Card component created${NC}"

# Continue with more components...
# This file is getting very long. Let me create it as part 1 and tell the user to run it

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Part 1 of code generation complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "⚠️  This script is split into multiple parts due to size."
echo "📝 Run generate-app-part2.sh next to continue..."
echo ""

