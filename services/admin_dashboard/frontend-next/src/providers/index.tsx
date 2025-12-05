/**
 * Unified Providers Component
 * 
 * Wraps the application with all necessary providers.
 */

'use client';

import { ReactNode } from 'react';
import { ThemeProvider } from './ThemeProvider';
import { SWRProvider } from './SWRProvider';
import { AuthProvider } from '@/hooks/useAuth';
import { NotificationsProvider } from '@/components/ui/notifications-center';

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      <SWRProvider>
        <AuthProvider>
          <NotificationsProvider>
            {children}
          </NotificationsProvider>
        </AuthProvider>
      </SWRProvider>
    </ThemeProvider>
  );
}

export default Providers;

