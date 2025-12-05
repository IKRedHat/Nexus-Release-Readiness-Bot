import type { Metadata, Viewport } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import '../styles/globals.css';
import { cn } from '@/lib/utils';
import { Providers } from '@/providers';
import { Toaster } from 'sonner';
import { Analytics } from '@vercel/analytics/react';
import { SkipLink } from '@/components/ui/skip-link';
import { GlobalComponents } from '@/components/GlobalComponents';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' });

export const metadata: Metadata = {
  title: {
    default: 'Nexus Admin Dashboard',
    template: '%s | Nexus Admin',
  },
  description: 'Enterprise-grade release automation platform',
  keywords: ['release automation', 'devops', 'admin dashboard', 'nexus'],
  authors: [{ name: 'Nexus Team' }],
  creator: 'Nexus',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://nexus-admin-dashboard.vercel.app',
    title: 'Nexus Admin Dashboard',
    description: 'Enterprise-grade release automation platform',
    siteName: 'Nexus Admin',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Nexus Admin Dashboard',
    description: 'Enterprise-grade release automation platform',
  },
  robots: {
    index: true,
    follow: true,
  },
  manifest: '/manifest.json',
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0a1a' },
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body
        className={cn(
          'min-h-screen bg-background font-sans antialiased',
          inter.variable,
          jetbrainsMono.variable
        )}
      >
        <Providers>
          {/* Skip to main content link for accessibility */}
          <SkipLink />
          
          {/* Main content */}
          {children}
          
          {/* Global components (Command Palette, Toasts, etc.) */}
          <GlobalComponents />
          
          {/* Toast notifications */}
          <Toaster 
            position="top-right" 
            richColors 
            closeButton
            toastOptions={{
              duration: 4000,
            }}
          />
          
          {/* Vercel Analytics */}
          <Analytics />
        </Providers>
      </body>
    </html>
  );
}
