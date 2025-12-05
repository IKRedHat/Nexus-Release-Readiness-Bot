/**
 * Global Components
 * 
 * Components that need to be available throughout the application:
 * - Command Palette
 * - Keyboard Shortcuts Modal
 * - Global Keyboard Handler
 */

'use client';

import { useState, useCallback } from 'react';
import { CommandPalette } from '@/components/ui/command-palette';
import { KeyboardShortcutsModal } from '@/components/ui/keyboard-shortcuts-modal';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

export function GlobalComponents() {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isShortcutsModalOpen, setIsShortcutsModalOpen] = useState(false);

  const handleOpenCommandPalette = useCallback(() => {
    setIsCommandPaletteOpen(true);
  }, []);

  const handleShowShortcuts = useCallback(() => {
    setIsShortcutsModalOpen(true);
  }, []);

  // Initialize keyboard shortcuts
  useKeyboardShortcuts({
    onOpenCommandPalette: handleOpenCommandPalette,
    onShowShortcuts: handleShowShortcuts,
  });

  return (
    <>
      {/* Command Palette */}
      <CommandPalette
        open={isCommandPaletteOpen}
        onOpenChange={setIsCommandPaletteOpen}
        onShowShortcuts={handleShowShortcuts}
      />

      {/* Keyboard Shortcuts Modal */}
      <KeyboardShortcutsModal
        open={isShortcutsModalOpen}
        onOpenChange={setIsShortcutsModalOpen}
      />
    </>
  );
}

export default GlobalComponents;

