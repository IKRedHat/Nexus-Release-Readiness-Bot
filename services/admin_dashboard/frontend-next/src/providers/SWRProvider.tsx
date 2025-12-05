/**
 * SWR Provider with Persistent Cache
 * 
 * Wraps the application with SWR configuration and persistent cache support.
 */

'use client';

import { ReactNode } from 'react';
import { SWRConfig } from 'swr';
import { swrConfig, createPersistentCache } from '@/lib/swr-config';

interface SWRProviderProps {
  children: ReactNode;
}

export function SWRProvider({ children }: SWRProviderProps) {
  return (
    <SWRConfig
      value={{
        ...swrConfig,
        provider: createPersistentCache(),
      }}
    >
      {children}
    </SWRConfig>
  );
}

export default SWRProvider;

