/**
 * Filter Persistence Hook
 * 
 * Provides URL-synced filters with saved presets.
 * Features:
 * - URL search params synchronization
 * - localStorage persistence
 * - Saved filter presets
 * - Type-safe filter values
 * - Debounced URL updates
 */

'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';

// =============================================================================
// Types
// =============================================================================

export interface FilterValue {
  [key: string]: string | string[] | number | boolean | null | undefined;
}

export interface FilterPreset<T extends FilterValue> {
  id: string;
  name: string;
  filters: T;
  isDefault?: boolean;
  createdAt: string;
}

export interface UseFiltersOptions<T extends FilterValue> {
  /** Default filter values */
  defaults: T;
  /** Local storage key for presets */
  storageKey: string;
  /** Sync filters to URL */
  syncToUrl?: boolean;
  /** Debounce URL updates (ms) */
  urlDebounce?: number;
  /** Keys to persist in URL (defaults to all) */
  urlKeys?: (keyof T)[];
}

export interface UseFiltersReturn<T extends FilterValue> {
  /** Current filter values */
  filters: T;
  /** Update a single filter */
  setFilter: <K extends keyof T>(key: K, value: T[K]) => void;
  /** Update multiple filters */
  setFilters: (updates: Partial<T>) => void;
  /** Reset filters to defaults */
  resetFilters: () => void;
  /** Clear all filters */
  clearFilters: () => void;
  /** Saved presets */
  presets: FilterPreset<T>[];
  /** Save current filters as preset */
  savePreset: (name: string) => void;
  /** Load a preset */
  loadPreset: (id: string) => void;
  /** Delete a preset */
  deletePreset: (id: string) => void;
  /** Set default preset */
  setDefaultPreset: (id: string | null) => void;
  /** Check if filters are modified from defaults */
  isModified: boolean;
  /** Active preset ID */
  activePresetId: string | null;
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useFilters<T extends FilterValue>(
  options: UseFiltersOptions<T>
): UseFiltersReturn<T> {
  const {
    defaults,
    storageKey,
    syncToUrl = true,
    urlDebounce = 300,
    urlKeys,
  } = options;

  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Initialize filters from URL or defaults
  const [filters, setFiltersState] = useState<T>(() => {
    if (typeof window === 'undefined' || !syncToUrl) return defaults;

    const urlFilters: Partial<T> = {};
    const keysToSync = urlKeys || (Object.keys(defaults) as (keyof T)[]);

    keysToSync.forEach((key) => {
      const urlValue = searchParams.get(String(key));
      if (urlValue !== null) {
        const defaultValue = defaults[key];
        
        // Parse based on default type
        if (Array.isArray(defaultValue)) {
          urlFilters[key] = urlValue.split(',') as T[keyof T];
        } else if (typeof defaultValue === 'number') {
          urlFilters[key] = Number(urlValue) as T[keyof T];
        } else if (typeof defaultValue === 'boolean') {
          urlFilters[key] = (urlValue === 'true') as T[keyof T];
        } else {
          urlFilters[key] = urlValue as T[keyof T];
        }
      }
    });

    return { ...defaults, ...urlFilters };
  });

  // Presets state
  const [presets, setPresets] = useState<FilterPreset<T>[]>([]);
  const [activePresetId, setActivePresetId] = useState<string | null>(null);

  // Load presets from localStorage
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const savedPresets = localStorage.getItem(`${storageKey}_presets`);
    if (savedPresets) {
      try {
        const parsed = JSON.parse(savedPresets) as FilterPreset<T>[];
        setPresets(parsed);

        // Load default preset if exists
        const defaultPreset = parsed.find(p => p.isDefault);
        if (defaultPreset && !searchParams.toString()) {
          setFiltersState({ ...defaults, ...defaultPreset.filters });
          setActivePresetId(defaultPreset.id);
        }
      } catch {
        // Invalid data, ignore
      }
    }
  }, [storageKey]); // eslint-disable-line react-hooks/exhaustive-deps

  // Sync filters to URL
  useEffect(() => {
    if (!syncToUrl || typeof window === 'undefined') return;

    const timeoutId = setTimeout(() => {
      const params = new URLSearchParams();
      const keysToSync = urlKeys || (Object.keys(defaults) as (keyof T)[]);

      keysToSync.forEach((key) => {
        const value = filters[key];
        const defaultValue = defaults[key];

        // Only include non-default values
        if (value !== undefined && value !== null && value !== defaultValue) {
          if (Array.isArray(value)) {
            if (value.length > 0) {
              params.set(String(key), value.join(','));
            }
          } else {
            params.set(String(key), String(value));
          }
        }
      });

      const queryString = params.toString();
      const newUrl = queryString ? `${pathname}?${queryString}` : pathname;
      
      // Only update if changed
      if (window.location.search !== `?${queryString}`) {
        router.replace(newUrl, { scroll: false });
      }
    }, urlDebounce);

    return () => clearTimeout(timeoutId);
  }, [filters, syncToUrl, urlDebounce, pathname, router, defaults, urlKeys]);

  // Update single filter
  const setFilter = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setFiltersState(prev => ({ ...prev, [key]: value }));
    setActivePresetId(null);
  }, []);

  // Update multiple filters
  const setFilters = useCallback((updates: Partial<T>) => {
    setFiltersState(prev => ({ ...prev, ...updates }));
    setActivePresetId(null);
  }, []);

  // Reset to defaults
  const resetFilters = useCallback(() => {
    setFiltersState(defaults);
    setActivePresetId(null);
  }, [defaults]);

  // Clear all filters (empty values)
  const clearFilters = useCallback(() => {
    const cleared = Object.keys(defaults).reduce((acc, key) => {
      const defaultValue = defaults[key as keyof T];
      if (Array.isArray(defaultValue)) {
        acc[key as keyof T] = [] as unknown as T[keyof T];
      } else if (typeof defaultValue === 'string') {
        acc[key as keyof T] = '' as T[keyof T];
      } else if (typeof defaultValue === 'number') {
        acc[key as keyof T] = 0 as T[keyof T];
      } else {
        acc[key as keyof T] = defaultValue;
      }
      return acc;
    }, {} as T);
    
    setFiltersState(cleared);
    setActivePresetId(null);
  }, [defaults]);

  // Save current filters as preset
  const savePreset = useCallback((name: string) => {
    const newPreset: FilterPreset<T> = {
      id: `preset_${Date.now()}`,
      name,
      filters: { ...filters },
      createdAt: new Date().toISOString(),
    };

    setPresets(prev => {
      const updated = [...prev, newPreset];
      localStorage.setItem(`${storageKey}_presets`, JSON.stringify(updated));
      return updated;
    });

    setActivePresetId(newPreset.id);
  }, [filters, storageKey]);

  // Load a preset
  const loadPreset = useCallback((id: string) => {
    const preset = presets.find(p => p.id === id);
    if (preset) {
      setFiltersState({ ...defaults, ...preset.filters });
      setActivePresetId(id);
    }
  }, [presets, defaults]);

  // Delete a preset
  const deletePreset = useCallback((id: string) => {
    setPresets(prev => {
      const updated = prev.filter(p => p.id !== id);
      localStorage.setItem(`${storageKey}_presets`, JSON.stringify(updated));
      return updated;
    });

    if (activePresetId === id) {
      setActivePresetId(null);
    }
  }, [storageKey, activePresetId]);

  // Set default preset
  const setDefaultPreset = useCallback((id: string | null) => {
    setPresets(prev => {
      const updated = prev.map(p => ({
        ...p,
        isDefault: p.id === id,
      }));
      localStorage.setItem(`${storageKey}_presets`, JSON.stringify(updated));
      return updated;
    });
  }, [storageKey]);

  // Check if filters are modified
  const isModified = useMemo(() => {
    return Object.keys(defaults).some(key => {
      const current = filters[key as keyof T];
      const defaultValue = defaults[key as keyof T];
      
      if (Array.isArray(current) && Array.isArray(defaultValue)) {
        return JSON.stringify(current) !== JSON.stringify(defaultValue);
      }
      return current !== defaultValue;
    });
  }, [filters, defaults]);

  return {
    filters,
    setFilter,
    setFilters,
    resetFilters,
    clearFilters,
    presets,
    savePreset,
    loadPreset,
    deletePreset,
    setDefaultPreset,
    isModified,
    activePresetId,
  };
}

export default useFilters;

