/**
 * Theme Toggle Component
 * 
 * A button to toggle between light, dark, and system themes.
 */

'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { Sun, Moon, Monitor, ChevronDown } from 'lucide-react';
import { Button } from './button';
import { cn } from '@/lib/utils';

interface ThemeToggleProps {
  variant?: 'button' | 'dropdown';
  className?: string;
}

export function ThemeToggle({ variant = 'button', className }: ThemeToggleProps) {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" className={cn('h-9 w-9', className)}>
        <div className="h-5 w-5 animate-pulse bg-muted rounded" />
      </Button>
    );
  }

  const themes = [
    { value: 'light', label: 'Light', icon: Sun },
    { value: 'dark', label: 'Dark', icon: Moon },
    { value: 'system', label: 'System', icon: Monitor },
  ];

  const currentTheme = themes.find((t) => t.value === theme) || themes[1];
  const CurrentIcon = currentTheme.icon;

  // Simple button variant - cycles through themes
  if (variant === 'button') {
    const cycleTheme = () => {
      const currentIndex = themes.findIndex((t) => t.value === theme);
      const nextIndex = (currentIndex + 1) % themes.length;
      setTheme(themes[nextIndex].value);
    };

    return (
      <Button
        variant="ghost"
        size="icon"
        onClick={cycleTheme}
        className={cn('h-9 w-9', className)}
        title={`Theme: ${currentTheme.label}`}
      >
        {resolvedTheme === 'dark' ? (
          <Moon className="h-5 w-5 text-muted-foreground" />
        ) : (
          <Sun className="h-5 w-5 text-muted-foreground" />
        )}
        <span className="sr-only">Toggle theme</span>
      </Button>
    );
  }

  // Dropdown variant - shows all options
  return (
    <div className={cn('relative', className)}>
      <Button
        variant="ghost"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 h-9 px-3"
      >
        <CurrentIcon className="h-4 w-4" />
        <span className="text-sm">{currentTheme.label}</span>
        <ChevronDown className={cn('h-4 w-4 transition-transform', isOpen && 'rotate-180')} />
      </Button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown menu */}
          <div className="absolute right-0 top-full mt-1 z-50 w-36 py-1 bg-card border border-border rounded-md shadow-lg">
            {themes.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                onClick={() => {
                  setTheme(value);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted transition-colors',
                  theme === value && 'bg-muted text-primary'
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
                {theme === value && (
                  <span className="ml-auto text-primary">✓</span>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default ThemeToggle;

