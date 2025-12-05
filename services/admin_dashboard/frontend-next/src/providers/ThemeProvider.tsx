/**
 * Theme Provider
 * 
 * Provides theme context for dark/light mode switching using next-themes.
 */

'use client';

import { ThemeProvider as NextThemesProvider } from 'next-themes';
import { ReactNode } from 'react';

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      disableTransitionOnChange={false}
      themes={['light', 'dark', 'system']}
    >
      {children}
    </NextThemesProvider>
  );
}

export default ThemeProvider;

