/**
 * Keyboard Shortcuts Modal
 * 
 * Displays available keyboard shortcuts in a modal dialog.
 */

'use client';

import { X, Keyboard } from 'lucide-react';
import { Button } from './button';
import { cn } from '@/lib/utils';
import { getModifierKey } from '@/hooks/useKeyboardShortcuts';

interface KeyboardShortcutsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const shortcuts = [
  {
    category: 'Navigation',
    items: [
      { keys: ['mod', 'D'], description: 'Go to Dashboard' },
      { keys: ['mod', 'Shift', 'R'], description: 'Go to Releases' },
      { keys: ['mod', 'Shift', 'H'], description: 'Go to Health' },
      { keys: ['mod', 'Shift', 'M'], description: 'Go to Metrics' },
      { keys: ['mod', 'Shift', 'S'], description: 'Go to Settings' },
      { keys: ['mod', 'Shift', 'A'], description: 'Go to Audit Log' },
    ],
  },
  {
    category: 'Actions',
    items: [
      { keys: ['mod', 'K'], description: 'Open Command Palette' },
      { keys: ['mod', '/'], description: 'Show Keyboard Shortcuts' },
      { keys: ['mod', 'B'], description: 'Toggle Sidebar' },
      { keys: ['Escape'], description: 'Close Modal / Dialog' },
    ],
  },
  {
    category: 'List Navigation (Vim-like)',
    items: [
      { keys: ['J'], description: 'Move down in list' },
      { keys: ['K'], description: 'Move up in list' },
      { keys: ['G', 'G'], description: 'Go to first item' },
      { keys: ['Shift', 'G'], description: 'Go to last item' },
      { keys: ['Enter'], description: 'Select / Open item' },
      { keys: ['E'], description: 'Edit selected item' },
      { keys: ['D'], description: 'Delete selected item' },
      { keys: ['/'], description: 'Focus search' },
    ],
  },
  {
    category: 'Forms',
    items: [
      { keys: ['Tab'], description: 'Move to next field' },
      { keys: ['Shift', 'Tab'], description: 'Move to previous field' },
      { keys: ['mod', 'Enter'], description: 'Submit form' },
      { keys: ['Escape'], description: 'Cancel / Close' },
    ],
  },
];

export function KeyboardShortcutsModal({ open, onOpenChange }: KeyboardShortcutsModalProps) {
  if (!open) return null;

  const mod = getModifierKey();

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm animate-in fade-in"
        onClick={() => onOpenChange(false)}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className={cn(
            'w-full max-w-lg bg-popover rounded-xl border border-border shadow-2xl overflow-hidden',
            'animate-in slide-in-from-bottom-4 fade-in duration-200'
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/50">
            <div className="flex items-center gap-3">
              <Keyboard className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">Keyboard Shortcuts</h2>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => onOpenChange(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Content */}
          <div className="p-6 max-h-[60vh] overflow-y-auto">
            <div className="space-y-6">
              {shortcuts.map((section) => (
                <div key={section.category}>
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">
                    {section.category}
                  </h3>
                  <div className="space-y-2">
                    {section.items.map((shortcut, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between py-2"
                      >
                        <span className="text-sm">{shortcut.description}</span>
                        <div className="flex items-center gap-1">
                          {shortcut.keys.map((key, keyIndex) => (
                            <kbd
                              key={keyIndex}
                              className={cn(
                                'h-6 min-w-6 flex items-center justify-center',
                                'px-2 rounded border border-border bg-muted',
                                'font-mono text-xs text-muted-foreground'
                              )}
                            >
                              {key === 'mod' ? mod : key}
                            </kbd>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-border bg-muted/50">
            <p className="text-xs text-muted-foreground text-center">
              Press <kbd className="px-1.5 py-0.5 rounded border bg-muted text-xs">{mod}K</kbd> to
              open the command palette for quick access
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

export default KeyboardShortcutsModal;

