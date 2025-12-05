/**
 * List Navigation Hook
 * 
 * Vim-like keyboard navigation for lists.
 * Features:
 * - J/K for up/down navigation
 * - Enter to select/open
 * - E to edit, D to delete
 * - / for search focus
 * - G to go to first/last (gg, G)
 * - Visual focus indicators
 */

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';

// =============================================================================
// Types
// =============================================================================

export interface ListNavigationOptions<T> {
  /** List of items */
  items: T[];
  /** Get unique ID from item */
  getItemId: (item: T) => string;
  /** Handle item selection (Enter) */
  onSelect?: (item: T) => void;
  /** Handle item edit (E) */
  onEdit?: (item: T) => void;
  /** Handle item delete (D) */
  onDelete?: (item: T) => void;
  /** Handle search focus (/) */
  onSearchFocus?: () => void;
  /** Handle escape */
  onEscape?: () => void;
  /** Enable/disable navigation */
  enabled?: boolean;
  /** Wrap around at ends */
  wrap?: boolean;
  /** Auto-scroll to focused item */
  autoScroll?: boolean;
}

export interface ListNavigationReturn<T> {
  /** Currently focused item ID */
  focusedId: string | null;
  /** Currently focused item */
  focusedItem: T | null;
  /** Focused item index */
  focusedIndex: number;
  /** Set focused item by ID */
  setFocusedId: (id: string | null) => void;
  /** Move focus up */
  focusPrevious: () => void;
  /** Move focus down */
  focusNext: () => void;
  /** Focus first item */
  focusFirst: () => void;
  /** Focus last item */
  focusLast: () => void;
  /** Check if item is focused */
  isFocused: (item: T) => boolean;
  /** Get props for list container */
  getContainerProps: () => React.HTMLAttributes<HTMLElement>;
  /** Get props for list item */
  getItemProps: (item: T) => React.HTMLAttributes<HTMLElement>;
  /** Ref for scroll container */
  containerRef: React.RefObject<HTMLElement>;
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useListNavigation<T>(
  options: ListNavigationOptions<T>
): ListNavigationReturn<T> {
  const {
    items,
    getItemId,
    onSelect,
    onEdit,
    onDelete,
    onSearchFocus,
    onEscape,
    enabled = true,
    wrap = true,
    autoScroll = true,
  } = options;

  const [focusedId, setFocusedId] = useState<string | null>(null);
  const containerRef = useRef<HTMLElement>(null);
  const itemRefs = useRef<Map<string, HTMLElement>>(new Map());
  const lastGPress = useRef<number>(0);

  // Get focused item and index
  const focusedIndex = focusedId 
    ? items.findIndex(item => getItemId(item) === focusedId)
    : -1;
  const focusedItem = focusedIndex >= 0 ? items[focusedIndex] : null;

  // Focus helpers
  const focusByIndex = useCallback((index: number) => {
    if (items.length === 0) return;
    
    let newIndex = index;
    if (wrap) {
      newIndex = ((index % items.length) + items.length) % items.length;
    } else {
      newIndex = Math.max(0, Math.min(index, items.length - 1));
    }
    
    const item = items[newIndex];
    if (item) {
      const id = getItemId(item);
      setFocusedId(id);

      // Auto-scroll
      if (autoScroll) {
        const element = itemRefs.current.get(id);
        element?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [items, getItemId, wrap, autoScroll]);

  const focusPrevious = useCallback(() => {
    focusByIndex(focusedIndex - 1);
  }, [focusByIndex, focusedIndex]);

  const focusNext = useCallback(() => {
    focusByIndex(focusedIndex === -1 ? 0 : focusedIndex + 1);
  }, [focusByIndex, focusedIndex]);

  const focusFirst = useCallback(() => {
    focusByIndex(0);
  }, [focusByIndex]);

  const focusLast = useCallback(() => {
    focusByIndex(items.length - 1);
  }, [focusByIndex, items.length]);

  const isFocused = useCallback((item: T) => {
    return getItemId(item) === focusedId;
  }, [getItemId, focusedId]);

  // Keyboard handler
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't capture when typing in inputs
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      switch (event.key.toLowerCase()) {
        // Navigation
        case 'j':
        case 'arrowdown':
          event.preventDefault();
          focusNext();
          break;

        case 'k':
        case 'arrowup':
          event.preventDefault();
          focusPrevious();
          break;

        // Go to first/last (vim: gg / G)
        case 'g':
          if (event.shiftKey) {
            // G - go to last
            event.preventDefault();
            focusLast();
          } else {
            // Check for gg (double g)
            const now = Date.now();
            if (now - lastGPress.current < 300) {
              event.preventDefault();
              focusFirst();
            }
            lastGPress.current = now;
          }
          break;

        case 'home':
          event.preventDefault();
          focusFirst();
          break;

        case 'end':
          event.preventDefault();
          focusLast();
          break;

        // Actions
        case 'enter':
        case ' ':
          if (focusedItem && onSelect) {
            event.preventDefault();
            onSelect(focusedItem);
          }
          break;

        case 'e':
          if (focusedItem && onEdit) {
            event.preventDefault();
            onEdit(focusedItem);
          }
          break;

        case 'd':
          if (focusedItem && onDelete && !event.metaKey && !event.ctrlKey) {
            event.preventDefault();
            onDelete(focusedItem);
          }
          break;

        // Search
        case '/':
          if (onSearchFocus) {
            event.preventDefault();
            onSearchFocus();
          }
          break;

        // Escape
        case 'escape':
          setFocusedId(null);
          onEscape?.();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    enabled,
    focusedItem,
    focusNext,
    focusPrevious,
    focusFirst,
    focusLast,
    onSelect,
    onEdit,
    onDelete,
    onSearchFocus,
    onEscape,
  ]);

  // Clear focus when items change
  useEffect(() => {
    if (focusedId && !items.some(item => getItemId(item) === focusedId)) {
      setFocusedId(null);
    }
  }, [items, focusedId, getItemId]);

  // Container props
  const getContainerProps = useCallback((): React.HTMLAttributes<HTMLElement> => ({
    role: 'listbox',
    tabIndex: 0,
    'aria-activedescendant': focusedId || undefined,
    onFocus: () => {
      if (!focusedId && items.length > 0) {
        setFocusedId(getItemId(items[0]));
      }
    },
  }), [focusedId, items, getItemId]);

  // Item props
  const getItemProps = useCallback((item: T): React.HTMLAttributes<HTMLElement> => {
    const id = getItemId(item);
    const focused = id === focusedId;

    return {
      id: `listitem-${id}`,
      role: 'option',
      'aria-selected': focused,
      tabIndex: focused ? 0 : -1,
      ref: (el: HTMLElement | null) => {
        if (el) {
          itemRefs.current.set(id, el);
        } else {
          itemRefs.current.delete(id);
        }
      },
      onClick: () => setFocusedId(id),
      onDoubleClick: () => {
        setFocusedId(id);
        if (onSelect) onSelect(item);
      },
    };
  }, [getItemId, focusedId, onSelect]);

  return {
    focusedId,
    focusedItem,
    focusedIndex,
    setFocusedId,
    focusPrevious,
    focusNext,
    focusFirst,
    focusLast,
    isFocused,
    getContainerProps,
    getItemProps,
    containerRef: containerRef as React.RefObject<HTMLElement>,
  };
}

// =============================================================================
// Focus Ring Component Styles
// =============================================================================

export const listItemFocusStyles = `
  data-[focused=true]:ring-2
  data-[focused=true]:ring-ring
  data-[focused=true]:ring-offset-2
  data-[focused=true]:ring-offset-background
  data-[focused=true]:bg-accent
`;

export default useListNavigation;

