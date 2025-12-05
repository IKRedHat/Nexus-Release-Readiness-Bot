/**
 * Next.js Middleware for Route Protection
 * 
 * Handles:
 * - Authentication checks
 * - Route protection
 * - Redirect logic
 * 
 * @see https://nextjs.org/docs/app/building-your-application/routing/middleware
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Public routes that don't require authentication
const PUBLIC_ROUTES = ['/login', '/auth', '/api/health'];

// Protected routes that require authentication
const PROTECTED_ROUTES = [
  '/',
  '/releases',
  '/health',
  '/metrics',
  '/settings',
  '/admin',
  '/feature-requests',
  '/debug',
];

// Admin-only routes that require elevated permissions
const ADMIN_ROUTES = ['/admin/users', '/admin/roles', '/settings'];

/**
 * Check if a path matches any pattern in the list
 */
function matchesPath(pathname: string, patterns: string[]): boolean {
  return patterns.some((pattern) => {
    if (pattern === pathname) return true;
    if (pattern.endsWith('*')) {
      return pathname.startsWith(pattern.slice(0, -1));
    }
    return pathname.startsWith(pattern + '/') || pathname === pattern;
  });
}

/**
 * Middleware function
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Get the token from cookie or authorization header
  const token = request.cookies.get('nexus_access_token')?.value ||
                request.headers.get('authorization')?.replace('Bearer ', '');
  
  // Allow static files and Next.js internals
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.') // Static files like .css, .js, .png
  ) {
    return NextResponse.next();
  }
  
  // Check if it's a public route
  const isPublicRoute = matchesPath(pathname, PUBLIC_ROUTES);
  
  // If on login page and already authenticated, redirect to dashboard
  if (isPublicRoute && pathname === '/login' && token) {
    return NextResponse.redirect(new URL('/', request.url));
  }
  
  // Allow public routes
  if (isPublicRoute) {
    return NextResponse.next();
  }
  
  // Check if it's a protected route
  const isProtectedRoute = matchesPath(pathname, PROTECTED_ROUTES);
  
  // If protected route and not authenticated, redirect to login
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  // For admin routes, we can add additional checks here
  // Note: Full permission checks should be done on the server/API level
  // This is just a first-line defense
  if (matchesPath(pathname, ADMIN_ROUTES) && !token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  // Add security headers
  const response = NextResponse.next();
  
  // Security headers
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('X-XSS-Protection', '1; mode=block');
  
  // Permissions policy
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=(), interest-cohort=()'
  );
  
  return response;
}

/**
 * Configure which paths the middleware runs on
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};

