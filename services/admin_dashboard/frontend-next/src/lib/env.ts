/**
 * Environment Variable Validation
 * 
 * Validates and exports typed environment variables.
 * Throws errors for missing required variables.
 */

/**
 * Get and validate environment variable
 */
function getEnvVar(key: string, defaultValue?: string): string {
  const value = process.env[key] || defaultValue;
  
  if (value === undefined) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  
  return value;
}

/**
 * Get optional environment variable
 */
function getOptionalEnvVar(key: string, defaultValue: string = ''): string {
  return process.env[key] || defaultValue;
}

/**
 * Validate URL format
 */
function validateUrl(value: string, varName: string): string {
  if (!value) return value;
  
  try {
    new URL(value);
    return value;
  } catch {
    console.warn(`Invalid URL for ${varName}: ${value}`);
    return value;
  }
}

/**
 * Environment configuration
 */
export const env = {
  // API Configuration
  apiUrl: validateUrl(
    getEnvVar('NEXT_PUBLIC_API_URL', 'https://nexus-admin-api-63b4.onrender.com'),
    'NEXT_PUBLIC_API_URL'
  ),
  
  // App Configuration
  appName: getOptionalEnvVar('NEXT_PUBLIC_APP_NAME', 'Nexus Admin Dashboard'),
  appVersion: getOptionalEnvVar('NEXT_PUBLIC_APP_VERSION', '3.0.0'),
  
  // Runtime Environment
  nodeEnv: getOptionalEnvVar('NODE_ENV', 'development') as 'development' | 'production' | 'test',
  isProduction: process.env.NODE_ENV === 'production',
  isDevelopment: process.env.NODE_ENV === 'development',
  isTest: process.env.NODE_ENV === 'test',
  
  // Feature Flags
  enableAnalytics: getOptionalEnvVar('NEXT_PUBLIC_ENABLE_ANALYTICS', 'true') === 'true',
  enableMockMode: getOptionalEnvVar('NEXT_PUBLIC_ENABLE_MOCK_MODE', 'true') === 'true',
  
  // Debug
  debug: getOptionalEnvVar('NEXT_PUBLIC_DEBUG', 'false') === 'true',
};

/**
 * Log environment configuration (development only)
 */
if (env.isDevelopment && typeof window !== 'undefined') {
  console.group('🔧 Environment Configuration');
  console.log('API URL:', env.apiUrl);
  console.log('App Name:', env.appName);
  console.log('App Version:', env.appVersion);
  console.log('Environment:', env.nodeEnv);
  console.log('Analytics:', env.enableAnalytics);
  console.log('Mock Mode:', env.enableMockMode);
  console.groupEnd();
}

export default env;

