/**
 * SWR Configuration with Persistent Cache
 * 
 * Provides:
 * - IndexedDB-based persistent cache
 * - Offline support
 * - Smart revalidation strategies
 * - Error retry logic
 */

'use client';

import { SWRConfiguration, Cache, State } from 'swr';
import { get, set, del, createStore, UseStore } from 'idb-keyval';

// IndexedDB store for SWR cache
let cacheStore: UseStore | null = null;

// Initialize the IndexedDB store
function getStore(): UseStore {
  if (!cacheStore && typeof window !== 'undefined') {
    cacheStore = createStore('nexus-swr-cache', 'cache');
  }
  return cacheStore!;
}

/**
 * Create a persistent cache provider using IndexedDB
 */
export function createPersistentCache(): () => Cache<unknown> {
  return () => {
    const map = new Map<string, State<unknown, unknown>>();
    
    return {
      get(key: string) {
        return map.get(key);
      },
      set(key: string, value: State<unknown, unknown>) {
        map.set(key, value);
        
        // Persist to IndexedDB (async, fire-and-forget)
        if (typeof window !== 'undefined' && value.data !== undefined) {
          const store = getStore();
          if (store) {
            set(key, {
              data: value.data,
              timestamp: Date.now(),
            }, store).catch(console.error);
          }
        }
      },
      delete(key: string) {
        map.delete(key);
        
        // Remove from IndexedDB
        if (typeof window !== 'undefined') {
          const store = getStore();
          if (store) {
            del(key, store).catch(console.error);
          }
        }
      },
      keys() {
        return map.keys();
      },
    };
  };
}

/**
 * Load cached data from IndexedDB
 */
export async function loadCachedData(key: string): Promise<unknown | null> {
  if (typeof window === 'undefined') return null;
  
  try {
    const store = getStore();
    if (!store) return null;
    
    const cached = await get(key, store) as { data: unknown; timestamp: number } | undefined;
    
    if (cached) {
      // Check if cache is still valid (24 hours)
      const maxAge = 24 * 60 * 60 * 1000;
      if (Date.now() - cached.timestamp < maxAge) {
        return cached.data;
      }
    }
  } catch (error) {
    console.error('Failed to load cached data:', error);
  }
  
  return null;
}

/**
 * Clear all cached data
 */
export async function clearCache(): Promise<void> {
  if (typeof window === 'undefined') return;
  
  try {
    const store = getStore();
    if (store) {
      // Clear all keys in the store
      const { clear } = await import('idb-keyval');
      await clear(store);
    }
  } catch (error) {
    console.error('Failed to clear cache:', error);
  }
}

/**
 * Default SWR configuration
 */
export const swrConfig: SWRConfiguration = {
  // Revalidation
  revalidateOnFocus: true,
  revalidateOnReconnect: true,
  revalidateIfStale: true,
  
  // Dedupe requests within 2 seconds
  dedupingInterval: 2000,
  
  // Keep data for 5 minutes before showing stale indicator
  focusThrottleInterval: 5000,
  
  // Error handling
  errorRetryCount: 3,
  errorRetryInterval: 5000,
  shouldRetryOnError: (error) => {
    // Don't retry on auth errors
    if (error?.response?.status === 401 || error?.response?.status === 403) {
      return false;
    }
    return true;
  },
  
  // Loading state
  loadingTimeout: 3000,
  
  // Global error handler
  onError: (error, key) => {
    if (process.env.NODE_ENV === 'development') {
      console.error(`SWR Error [${key}]:`, error);
    }
  },
  
  // Global success handler for debugging
  onSuccess: (data, key) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`SWR Success [${key}]:`, data);
    }
  },
};

/**
 * Configuration for real-time data (health checks, metrics)
 */
export const realtimeConfig: SWRConfiguration = {
  ...swrConfig,
  refreshInterval: 10000, // 10 seconds
  revalidateOnFocus: true,
  dedupingInterval: 5000,
};

/**
 * Configuration for static data (users, roles, config)
 */
export const staticConfig: SWRConfiguration = {
  ...swrConfig,
  refreshInterval: 0, // Manual refresh only
  revalidateOnFocus: false,
  dedupingInterval: 60000, // 1 minute
};

/**
 * Configuration for dashboard data
 */
export const dashboardConfig: SWRConfiguration = {
  ...swrConfig,
  refreshInterval: 30000, // 30 seconds
  revalidateOnFocus: true,
  dedupingInterval: 10000,
};

export default swrConfig;

