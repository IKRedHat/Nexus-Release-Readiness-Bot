/**
 * Command Palette Component
 * 
 * A global command palette for quick navigation and actions.
 * Triggered by Cmd/Ctrl + K.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Command } from 'cmdk';
import {
  Home,
  Package,
  Activity,
  BarChart3,
  Settings,
  Users,
  Shield,
  FileText,
  Search,
  Moon,
  Sun,
  LogOut,
  Plus,
  RefreshCw,
  Keyboard,
  HelpCircle,
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { cn } from '@/lib/utils';
import { getModifierKey } from '@/hooks/useKeyboardShortcuts';

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onShowShortcuts?: () => void;
}

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ElementType;
  shortcut?: string;
  action: () => void;
  keywords?: string[];
  category: 'navigation' | 'actions' | 'theme' | 'help';
}

export function CommandPalette({ open, onOpenChange, onShowShortcuts }: CommandPaletteProps) {
  const router = useRouter();
  const { setTheme, resolvedTheme } = useTheme();
  const [search, setSearch] = useState('');

  const closeAndNavigate = useCallback(
    (path: string) => {
      onOpenChange(false);
      router.push(path);
    },
    [onOpenChange, router]
  );

  const closeAndExecute = useCallback(
    (action: () => void) => {
      onOpenChange(false);
      action();
    },
    [onOpenChange]
  );

  const mod = getModifierKey();

  const commands: CommandItem[] = [
    // Navigation
    {
      id: 'dashboard',
      label: 'Dashboard',
      description: 'Go to main dashboard',
      icon: Home,
      shortcut: `${mod}D`,
      action: () => closeAndNavigate('/'),
      keywords: ['home', 'main', 'overview'],
      category: 'navigation',
    },
    {
      id: 'releases',
      label: 'Releases',
      description: 'View release management',
      icon: Package,
      shortcut: `${mod}⇧R`,
      action: () => closeAndNavigate('/releases'),
      keywords: ['deployment', 'version'],
      category: 'navigation',
    },
    {
      id: 'health',
      label: 'Health Monitor',
      description: 'Check system health status',
      icon: Activity,
      shortcut: `${mod}⇧H`,
      action: () => closeAndNavigate('/health'),
      keywords: ['status', 'uptime', 'monitoring'],
      category: 'navigation',
    },
    {
      id: 'metrics',
      label: 'Metrics',
      description: 'View system metrics',
      icon: BarChart3,
      shortcut: `${mod}⇧M`,
      action: () => closeAndNavigate('/metrics'),
      keywords: ['analytics', 'statistics', 'performance'],
      category: 'navigation',
    },
    {
      id: 'feature-requests',
      label: 'Feature Requests',
      description: 'Manage feature requests',
      icon: FileText,
      action: () => closeAndNavigate('/feature-requests'),
      keywords: ['tickets', 'requests'],
      category: 'navigation',
    },
    {
      id: 'settings',
      label: 'Settings',
      description: 'Configure system settings',
      icon: Settings,
      shortcut: `${mod}⇧S`,
      action: () => closeAndNavigate('/settings'),
      keywords: ['config', 'configuration', 'preferences'],
      category: 'navigation',
    },
    {
      id: 'users',
      label: 'User Management',
      description: 'Manage users and access',
      icon: Users,
      action: () => closeAndNavigate('/admin/users'),
      keywords: ['accounts', 'permissions'],
      category: 'navigation',
    },
    {
      id: 'roles',
      label: 'Role Management',
      description: 'Manage roles and permissions',
      icon: Shield,
      action: () => closeAndNavigate('/admin/roles'),
      keywords: ['rbac', 'permissions', 'access'],
      category: 'navigation',
    },

    // Actions
    {
      id: 'new-release',
      label: 'New Release',
      description: 'Create a new release',
      icon: Plus,
      action: () => closeAndNavigate('/releases?action=new'),
      keywords: ['create', 'add'],
      category: 'actions',
    },
    {
      id: 'new-feature',
      label: 'New Feature Request',
      description: 'Submit a feature request',
      icon: Plus,
      action: () => closeAndNavigate('/feature-requests?action=new'),
      keywords: ['create', 'add', 'ticket'],
      category: 'actions',
    },
    {
      id: 'refresh',
      label: 'Refresh Data',
      description: 'Refresh all cached data',
      icon: RefreshCw,
      action: () => {
        window.location.reload();
      },
      keywords: ['reload', 'update'],
      category: 'actions',
    },

    // Theme
    {
      id: 'theme-light',
      label: 'Light Theme',
      description: 'Switch to light mode',
      icon: Sun,
      action: () => closeAndExecute(() => setTheme('light')),
      keywords: ['mode', 'appearance'],
      category: 'theme',
    },
    {
      id: 'theme-dark',
      label: 'Dark Theme',
      description: 'Switch to dark mode',
      icon: Moon,
      action: () => closeAndExecute(() => setTheme('dark')),
      keywords: ['mode', 'appearance'],
      category: 'theme',
    },

    // Help
    {
      id: 'keyboard-shortcuts',
      label: 'Keyboard Shortcuts',
      description: 'View all keyboard shortcuts',
      icon: Keyboard,
      shortcut: `${mod}/`,
      action: () => closeAndExecute(() => onShowShortcuts?.()),
      keywords: ['hotkeys', 'keys'],
      category: 'help',
    },
    {
      id: 'help',
      label: 'Help & Documentation',
      description: 'View documentation',
      icon: HelpCircle,
      action: () => window.open('https://github.com/IKRedHat/Nexus-Release-Readiness-Bot', '_blank'),
      keywords: ['docs', 'guide'],
      category: 'help',
    },
  ];

  // Clear search when closing
  useEffect(() => {
    if (!open) {
      setSearch('');
    }
  }, [open]);

  // Handle keyboard shortcut to open
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onOpenChange(!open);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onOpenChange]);

  const groupedCommands = {
    navigation: commands.filter((c) => c.category === 'navigation'),
    actions: commands.filter((c) => c.category === 'actions'),
    theme: commands.filter((c) => c.category === 'theme'),
    help: commands.filter((c) => c.category === 'help'),
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm animate-in fade-in"
        onClick={() => onOpenChange(false)}
      />

      {/* Command Dialog */}
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
        <Command
          className={cn(
            'w-full max-w-xl bg-popover rounded-xl border border-border shadow-2xl overflow-hidden',
            'animate-in slide-in-from-top-4 fade-in duration-200'
          )}
          loop
        >
          {/* Search Input */}
          <div className="flex items-center border-b border-border px-4">
            <Search className="h-4 w-4 text-muted-foreground mr-2 shrink-0" />
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Type a command or search..."
              className="flex-1 h-12 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none"
            />
            <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border border-border bg-muted px-1.5 font-mono text-xs text-muted-foreground">
              ESC
            </kbd>
          </div>

          {/* Command List */}
          <Command.List className="max-h-[300px] overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
              No results found.
            </Command.Empty>

            {/* Navigation */}
            {groupedCommands.navigation.length > 0 && (
              <Command.Group heading="Navigation" className="text-xs text-muted-foreground px-2 py-1.5">
                {groupedCommands.navigation.map((command) => (
                  <CommandItem key={command.id} command={command} />
                ))}
              </Command.Group>
            )}

            {/* Actions */}
            {groupedCommands.actions.length > 0 && (
              <Command.Group heading="Actions" className="text-xs text-muted-foreground px-2 py-1.5">
                {groupedCommands.actions.map((command) => (
                  <CommandItem key={command.id} command={command} />
                ))}
              </Command.Group>
            )}

            {/* Theme */}
            {groupedCommands.theme.length > 0 && (
              <Command.Group heading="Theme" className="text-xs text-muted-foreground px-2 py-1.5">
                {groupedCommands.theme.map((command) => (
                  <CommandItem key={command.id} command={command} />
                ))}
              </Command.Group>
            )}

            {/* Help */}
            {groupedCommands.help.length > 0 && (
              <Command.Group heading="Help" className="text-xs text-muted-foreground px-2 py-1.5">
                {groupedCommands.help.map((command) => (
                  <CommandItem key={command.id} command={command} />
                ))}
              </Command.Group>
            )}
          </Command.List>

          {/* Footer */}
          <div className="border-t border-border px-4 py-2 text-xs text-muted-foreground flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="h-5 min-w-5 flex items-center justify-center rounded border bg-muted px-1">↑</kbd>
                <kbd className="h-5 min-w-5 flex items-center justify-center rounded border bg-muted px-1">↓</kbd>
                <span>Navigate</span>
              </span>
              <span className="flex items-center gap-1">
                <kbd className="h-5 min-w-5 flex items-center justify-center rounded border bg-muted px-1">↵</kbd>
                <span>Select</span>
              </span>
            </div>
            <span>{mod}K to toggle</span>
          </div>
        </Command>
      </div>
    </>
  );
}

function CommandItem({ command }: { command: CommandItem }) {
  const Icon = command.icon;

  return (
    <Command.Item
      value={`${command.label} ${command.description} ${command.keywords?.join(' ')}`}
      onSelect={command.action}
      className={cn(
        'flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer',
        'text-sm text-foreground',
        'aria-selected:bg-accent aria-selected:text-accent-foreground',
        'transition-colors'
      )}
    >
      <Icon className="h-4 w-4 text-muted-foreground" />
      <div className="flex-1">
        <div className="font-medium">{command.label}</div>
        {command.description && (
          <div className="text-xs text-muted-foreground">{command.description}</div>
        )}
      </div>
      {command.shortcut && (
        <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border border-border bg-muted px-1.5 font-mono text-xs text-muted-foreground">
          {command.shortcut}
        </kbd>
      )}
    </Command.Item>
  );
}

export default CommandPalette;

