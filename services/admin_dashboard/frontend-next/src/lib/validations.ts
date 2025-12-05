/**
 * Form Validation Schemas
 * 
 * Zod schemas for form validation throughout the application.
 */

import { z } from 'zod';

// =============================================================================
// Auth Schemas
// =============================================================================

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(6, 'Password must be at least 6 characters'),
  rememberMe: z.boolean().optional(),
});

export type LoginFormData = z.infer<typeof loginSchema>;

// =============================================================================
// Release Schemas
// =============================================================================

export const releaseSchema = z.object({
  name: z
    .string()
    .min(1, 'Release name is required')
    .max(100, 'Release name must be less than 100 characters'),
  version: z
    .string()
    .min(1, 'Version is required')
    .regex(/^\d+\.\d+\.\d+$/, 'Version must be in format X.Y.Z (e.g., 1.0.0)'),
  description: z
    .string()
    .max(1000, 'Description must be less than 1000 characters')
    .optional(),
  status: z.enum(['planned', 'in_progress', 'completed', 'cancelled']),
  release_date: z
    .string()
    .min(1, 'Release date is required'),
  risk_level: z.enum(['low', 'medium', 'high']).optional(),
  owner: z.string().optional(),
  features: z.array(z.string()).optional(),
  bugs_fixed: z.array(z.string()).optional(),
});

export type ReleaseFormData = z.infer<typeof releaseSchema>;

// =============================================================================
// Feature Request Schemas
// =============================================================================

export const featureRequestSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required')
    .max(200, 'Title must be less than 200 characters'),
  description: z
    .string()
    .min(10, 'Description must be at least 10 characters')
    .max(5000, 'Description must be less than 5000 characters'),
  priority: z.enum(['low', 'medium', 'high', 'critical']),
  status: z.enum(['pending', 'approved', 'rejected', 'implemented', 'in_progress']).optional(),
  labels: z.array(z.string()).optional(),
  jira_ticket: z.string().optional(),
});

export type FeatureRequestFormData = z.infer<typeof featureRequestSchema>;

// =============================================================================
// User Schemas
// =============================================================================

export const userSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  name: z
    .string()
    .min(1, 'Name is required')
    .max(100, 'Name must be less than 100 characters'),
  roles: z
    .array(z.string())
    .min(1, 'At least one role is required'),
  is_active: z.boolean(),
  is_admin: z.boolean().optional(),
});

export type UserFormData = z.infer<typeof userSchema>;

// =============================================================================
// Role Schemas
// =============================================================================

export const roleSchema = z.object({
  name: z
    .string()
    .min(1, 'Role name is required')
    .max(50, 'Role name must be less than 50 characters')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Role name can only contain letters, numbers, underscores, and hyphens'),
  description: z
    .string()
    .max(500, 'Description must be less than 500 characters')
    .optional(),
  permissions: z
    .array(z.string())
    .min(1, 'At least one permission is required'),
});

export type RoleFormData = z.infer<typeof roleSchema>;

// =============================================================================
// Configuration Schemas
// =============================================================================

export const jiraConfigSchema = z.object({
  enabled: z.boolean(),
  url: z.string().url('Please enter a valid URL').optional().or(z.literal('')),
  project_key: z.string().optional(),
  api_token: z.string().optional(),
  email: z.string().email('Please enter a valid email').optional().or(z.literal('')),
});

export type JiraConfigFormData = z.infer<typeof jiraConfigSchema>;

export const githubConfigSchema = z.object({
  enabled: z.boolean(),
  token: z.string().optional(),
  repo: z.string().optional(),
  owner: z.string().optional(),
});

export type GitHubConfigFormData = z.infer<typeof githubConfigSchema>;

export const slackConfigSchema = z.object({
  enabled: z.boolean(),
  webhook_url: z.string().url('Please enter a valid webhook URL').optional().or(z.literal('')),
  channel: z.string().optional(),
});

export type SlackConfigFormData = z.infer<typeof slackConfigSchema>;

// =============================================================================
// Search & Filter Schemas
// =============================================================================

export const searchSchema = z.object({
  query: z.string().max(200, 'Search query too long'),
  filters: z.object({
    status: z.array(z.string()).optional(),
    priority: z.array(z.string()).optional(),
    dateFrom: z.string().optional(),
    dateTo: z.string().optional(),
  }).optional(),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).optional(),
});

export type SearchFormData = z.infer<typeof searchSchema>;

// =============================================================================
// Helper Schemas
// =============================================================================

// URL validation
export const urlSchema = z.string().url('Please enter a valid URL');

// Email validation
export const emailSchema = z.string().email('Please enter a valid email');

// Password validation
export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number');

// Password confirmation
export const passwordConfirmSchema = z
  .object({
    password: passwordSchema,
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export default {
  loginSchema,
  releaseSchema,
  featureRequestSchema,
  userSchema,
  roleSchema,
  jiraConfigSchema,
  githubConfigSchema,
  slackConfigSchema,
  searchSchema,
};

