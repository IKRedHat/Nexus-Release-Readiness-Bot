/** @type {import('next').NextConfig} */
import bundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://nexus-admin-api-63b4.onrender.com';

// Content Security Policy
const ContentSecurityPolicy = `
  default-src 'self';
  script-src 'self' 'unsafe-eval' 'unsafe-inline' https://va.vercel-scripts.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https: blob:;
  font-src 'self' data:;
  connect-src 'self' ${API_URL} https://*.onrender.com https://*.vercel-analytics.com https://vitals.vercel-insights.com;
  frame-ancestors 'none';
  form-action 'self';
  base-uri 'self';
  upgrade-insecure-requests;
`.replace(/\s{2,}/g, ' ').trim();

const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: ContentSecurityPolicy,
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block',
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=31536000; includeSubDomains',
  },
];

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  poweredByHeader: false,
  compress: true,
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: API_URL,
    NEXT_PUBLIC_APP_NAME: 'Nexus Admin Dashboard',
    NEXT_PUBLIC_APP_VERSION: '3.0.0',
  },
  
  // Compiler options
  compiler: {
    // Remove console logs in production
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },
  
  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 60,
  },
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },
  
  // Redirects
  async redirects() {
    return [
      // Redirect old paths if any
      {
        source: '/dashboard',
        destination: '/',
        permanent: true,
      },
      {
        source: '/config',
        destination: '/settings',
        permanent: true,
      },
      {
        source: '/configuration',
        destination: '/settings',
        permanent: true,
      },
    ];
  },
  
  // Performance optimizations
  experimental: {
    // Enable optimized package imports
    optimizePackageImports: ['lucide-react', 'recharts', 'date-fns', '@tanstack/react-table', 'cmdk'],
  },
  
  // Logging configuration
  logging: {
    fetches: {
      fullUrl: process.env.NODE_ENV === 'development',
    },
  },
};

export default withBundleAnalyzer(nextConfig);
