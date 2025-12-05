/**
 * Filter Presets Component
 * 
 * UI for managing saved filter presets.
 */

'use client';

import { useState } from 'react';
import {
  Bookmark,
  BookmarkPlus,
  Star,
  Trash2,
  ChevronDown,
  Check,
} from 'lucide-react';
import { Button } from './button';
import { Input } from './input';
import { Badge } from './badge';
import { cn } from '@/lib/utils';
import type { FilterPreset, FilterValue } from '@/hooks/useFilters';

interface FilterPresetsProps<T extends FilterValue> {
  presets: FilterPreset<T>[];
  activePresetId: string | null;
  onLoadPreset: (id: string) => void;
  onSavePreset: (name: string) => void;
  onDeletePreset: (id: string) => void;
  onSetDefault: (id: string | null) => void;
  canSave?: boolean;
  className?: string;
}

export function FilterPresets<T extends FilterValue>({
  presets,
  activePresetId,
  onLoadPreset,
  onSavePreset,
  onDeletePreset,
  onSetDefault,
  canSave = true,
  className,
}: FilterPresetsProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [newPresetName, setNewPresetName] = useState('');

  const handleSave = () => {
    if (!newPresetName.trim()) return;
    onSavePreset(newPresetName.trim());
    setNewPresetName('');
    setIsSaving(false);
  };

  const activePreset = presets.find(p => p.id === activePresetId);

  return (
    <div className={cn('relative', className)}>
      {/* Trigger Button */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'gap-2',
          activePreset && 'border-primary text-primary'
        )}
      >
        <Bookmark className="h-4 w-4" />
        {activePreset ? activePreset.name : 'Presets'}
        {presets.length > 0 && (
          <Badge variant="secondary" className="ml-1">
            {presets.length}
          </Badge>
        )}
        <ChevronDown className={cn(
          'h-4 w-4 transition-transform',
          isOpen && 'rotate-180'
        )} />
      </Button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => {
              setIsOpen(false);
              setIsSaving(false);
            }}
          />

          {/* Menu */}
          <div className="absolute left-0 top-full mt-1 z-50 w-64 bg-popover border border-border rounded-lg shadow-lg overflow-hidden">
            {/* Header */}
            <div className="px-3 py-2 border-b border-border bg-muted/50">
              <span className="text-sm font-medium">Saved Filters</span>
            </div>

            {/* Presets List */}
            <div className="max-h-60 overflow-y-auto">
              {presets.length === 0 ? (
                <div className="px-3 py-6 text-center text-sm text-muted-foreground">
                  No saved presets yet
                </div>
              ) : (
                presets.map(preset => (
                  <div
                    key={preset.id}
                    className={cn(
                      'flex items-center gap-2 px-3 py-2 hover:bg-muted cursor-pointer group',
                      activePresetId === preset.id && 'bg-primary/10'
                    )}
                    onClick={() => {
                      onLoadPreset(preset.id);
                      setIsOpen(false);
                    }}
                  >
                    {/* Default Star */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSetDefault(preset.isDefault ? null : preset.id);
                      }}
                      className="text-muted-foreground hover:text-yellow-500"
                    >
                      <Star
                        className={cn(
                          'h-4 w-4',
                          preset.isDefault && 'fill-yellow-500 text-yellow-500'
                        )}
                      />
                    </button>

                    {/* Name */}
                    <div className="flex-1 min-w-0">
                      <span className="text-sm truncate block">{preset.name}</span>
                    </div>

                    {/* Active Indicator */}
                    {activePresetId === preset.id && (
                      <Check className="h-4 w-4 text-primary" />
                    )}

                    {/* Delete */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeletePreset(preset.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))
              )}
            </div>

            {/* Save New */}
            {canSave && (
              <div className="border-t border-border p-2">
                {isSaving ? (
                  <div className="flex items-center gap-2">
                    <Input
                      placeholder="Preset name..."
                      value={newPresetName}
                      onChange={(e) => setNewPresetName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSave();
                        if (e.key === 'Escape') setIsSaving(false);
                      }}
                      autoFocus
                      className="h-8 text-sm"
                    />
                    <Button size="sm" className="h-8" onClick={handleSave}>
                      Save
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={() => setIsSaving(true)}
                  >
                    <BookmarkPlus className="h-4 w-4 mr-2" />
                    Save Current Filters
                  </Button>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default FilterPresets;

