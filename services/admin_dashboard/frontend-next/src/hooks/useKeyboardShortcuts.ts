/**
 * Keyboard Shortcuts Hook
 * 
 * Provides global keyboard shortcut handling for the application.
 * 
 * Shortcuts:
 * - Cmd/Ctrl + K: Open command palette
 * - Cmd/Ctrl + /: Show keyboard shortcuts
 * - Cmd/Ctrl + B: Toggle sidebar
 * - Cmd/Ctrl + D: Go to dashboard
 * - Cmd/Ctrl + R: Go to releases
 * - Cmd/Ctrl + H: Go to health
 * - Cmd/Ctrl + S: Go to settings
 * - Escape: Close modals/dialogs
 */

'use client';

import { useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description: string;
  category?: string;
}

// Platform detection
const isMac = typeof window !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;

// Default shortcuts
const DEFAULT_SHORTCUTS: KeyboardShortcut[] = [
  // Navigation
  {
    key: 'd',
    meta: true,
    ctrl: true,
    action: () => {},
    description: 'Go to Dashboard',
    category: 'Navigation',
  },
  {
    key: 'r',
    meta: true,
    ctrl: true,
    shift: true,
    action: () => {},
    description: 'Go to Releases',
    category: 'Navigation',
  },
  {
    key: 'h',
    meta: true,
    ctrl: true,
    shift: true,
    action: () => {},
    description: 'Go to Health',
    category: 'Navigation',
  },
  // Actions
  {
    key: 'k',
    meta: true,
    ctrl: true,
    action: () => {},
    description: 'Open Command Palette',
    category: 'Actions',
  },
  {
    key: '/',
    meta: true,
    ctrl: true,
    action: () => {},
    description: 'Show Keyboard Shortcuts',
    category: 'Actions',
  },
  {
    key: 'b',
    meta: true,
    ctrl: true,
    action: () => {},
    description: 'Toggle Sidebar',
    category: 'Actions',
  },
];

interface UseKeyboardShortcutsOptions {
  onOpenCommandPalette?: () => void;
  onShowShortcuts?: () => void;
  onToggleSidebar?: () => void;
  enabled?: boolean;
  customShortcuts?: KeyboardShortcut[];
}

export function useKeyboardShortcuts({
  onOpenCommandPalette,
  onShowShortcuts,
  onToggleSidebar,
  enabled = true,
  customShortcuts = [],
}: UseKeyboardShortcutsOptions = {}) {
  const router = useRouter();
  const shortcutsRef = useRef<KeyboardShortcut[]>([]);

  // Build shortcuts with actions
  useEffect(() => {
    shortcutsRef.current = [
      // Navigation shortcuts
      {
        key: 'd',
        meta: true,
        ctrl: true,
        action: () => router.push('/'),
        description: 'Go to Dashboard',
        category: 'Navigation',
      },
      {
        key: 'r',
        meta: true,
        ctrl: true,
        shift: true,
        action: () => router.push('/releases'),
        description: 'Go to Releases',
        category: 'Navigation',
      },
      {
        key: 'h',
        meta: true,
        ctrl: true,
        shift: true,
        action: () => router.push('/health'),
        description: 'Go to Health',
        category: 'Navigation',
      },
      {
        key: 'm',
        meta: true,
        ctrl: true,
        shift: true,
        action: () => router.push('/metrics'),
        description: 'Go to Metrics',
        category: 'Navigation',
      },
      {
        key: 's',
        meta: true,
        ctrl: true,
        shift: true,
        action: () => router.push('/settings'),
        description: 'Go to Settings',
        category: 'Navigation',
      },
      // Action shortcuts
      {
        key: 'k',
        meta: true,
        ctrl: true,
        action: () => onOpenCommandPalette?.(),
        description: 'Open Command Palette',
        category: 'Actions',
      },
      {
        key: '/',
        meta: true,
        ctrl: true,
        action: () => onShowShortcuts?.(),
        description: 'Show Keyboard Shortcuts',
        category: 'Actions',
      },
      {
        key: 'b',
        meta: true,
        ctrl: true,
        action: () => onToggleSidebar?.(),
        description: 'Toggle Sidebar',
        category: 'Actions',
      },
      // Add custom shortcuts
      ...customShortcuts,
    ];
  }, [router, onOpenCommandPalette, onShowShortcuts, onToggleSidebar, customShortcuts]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        // Allow Escape to work in inputs
        if (event.key !== 'Escape') return;
      }

      const shortcut = shortcutsRef.current.find((s) => {
        const keyMatch = s.key.toLowerCase() === event.key.toLowerCase();
        const metaMatch = isMac ? (s.meta ? event.metaKey : !event.metaKey) : true;
        const ctrlMatch = !isMac ? (s.ctrl ? event.ctrlKey : !event.ctrlKey) : (s.ctrl ? event.ctrlKey : !event.ctrlKey);
        const shiftMatch = s.shift ? event.shiftKey : !event.shiftKey;
        const altMatch = s.alt ? event.altKey : !event.altKey;

        // For shortcuts with both meta and ctrl, check if either is pressed (cross-platform)
        if (s.meta && s.ctrl) {
          return keyMatch && (event.metaKey || event.ctrlKey) && shiftMatch && altMatch;
        }

        return keyMatch && metaMatch && ctrlMatch && shiftMatch && altMatch;
      });

      if (shortcut) {
        event.preventDefault();
        shortcut.action();
      }
    },
    [enabled]
  );

  useEffect(() => {
    if (!enabled) return;

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown, enabled]);

  return {
    shortcuts: shortcutsRef.current,
    isMac,
  };
}

/**
 * Get the modifier key symbol for the current platform
 */
export function getModifierKey(): string {
  return isMac ? '⌘' : 'Ctrl';
}

/**
 * Format a shortcut for display
 */
export function formatShortcut(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];

  if (shortcut.ctrl || shortcut.meta) {
    parts.push(getModifierKey());
  }
  if (shortcut.shift) {
    parts.push(isMac ? '⇧' : 'Shift');
  }
  if (shortcut.alt) {
    parts.push(isMac ? '⌥' : 'Alt');
  }
  parts.push(shortcut.key.toUpperCase());

  return parts.join(isMac ? '' : '+');
}

/**
 * Group shortcuts by category
 */
export function groupShortcuts(shortcuts: KeyboardShortcut[]): Record<string, KeyboardShortcut[]> {
  return shortcuts.reduce((acc, shortcut) => {
    const category = shortcut.category || 'General';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(shortcut);
    return acc;
  }, {} as Record<string, KeyboardShortcut[]>);
}

export default useKeyboardShortcuts;

