/**
 * Dashboard Grid Component with Drag & Drop
 * 
 * A customizable dashboard grid that allows users to:
 * - Drag and drop widgets to reorder
 * - Resize widgets
 * - Toggle widget visibility
 * - Save custom layouts
 */

'use client';

import { useState, useCallback, useEffect, ReactNode } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  rectSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  GripVertical,
  Eye,
  EyeOff,
  Settings2,
  RotateCcw,
  Save,
  X,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// =============================================================================
// Types
// =============================================================================

export interface DashboardWidget {
  id: string;
  title: string;
  component: ReactNode;
  size: 'small' | 'medium' | 'large' | 'full';
  visible: boolean;
  minSize?: 'small' | 'medium' | 'large';
}

interface DashboardGridProps {
  widgets: DashboardWidget[];
  onLayoutChange?: (widgets: DashboardWidget[]) => void;
  editable?: boolean;
  className?: string;
}

interface SortableWidgetProps {
  widget: DashboardWidget;
  isEditing: boolean;
  onToggleVisibility: (id: string) => void;
  onResize: (id: string, size: DashboardWidget['size']) => void;
}

// =============================================================================
// Size Configuration
// =============================================================================

const SIZE_CLASSES: Record<DashboardWidget['size'], string> = {
  small: 'col-span-1',
  medium: 'col-span-1 md:col-span-2',
  large: 'col-span-1 md:col-span-2 lg:col-span-3',
  full: 'col-span-1 md:col-span-2 lg:col-span-4',
};

const SIZE_OPTIONS: { value: DashboardWidget['size']; label: string }[] = [
  { value: 'small', label: 'S' },
  { value: 'medium', label: 'M' },
  { value: 'large', label: 'L' },
  { value: 'full', label: 'Full' },
];

// =============================================================================
// Local Storage Key
// =============================================================================

const STORAGE_KEY = 'nexus_dashboard_layout';

// =============================================================================
// Sortable Widget Component
// =============================================================================

function SortableWidget({
  widget,
  isEditing,
  onToggleVisibility,
  onResize,
}: SortableWidgetProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: widget.id, disabled: !isEditing });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  if (!widget.visible && !isEditing) {
    return null;
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        SIZE_CLASSES[widget.size],
        !widget.visible && 'opacity-50'
      )}
    >
      <Card className={cn(
        'h-full transition-all',
        isDragging && 'shadow-2xl ring-2 ring-primary',
        isEditing && 'ring-1 ring-border hover:ring-primary'
      )}>
        {/* Widget Header */}
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between text-base">
            <div className="flex items-center gap-2">
              {isEditing && (
                <button
                  {...attributes}
                  {...listeners}
                  className="cursor-grab active:cursor-grabbing p-1 hover:bg-muted rounded"
                >
                  <GripVertical className="w-4 h-4 text-muted-foreground" />
                </button>
              )}
              <span className={cn(!widget.visible && 'text-muted-foreground')}>
                {widget.title}
              </span>
            </div>

            {/* Edit Controls */}
            {isEditing && (
              <div className="flex items-center gap-1">
                {/* Size Selector */}
                <div className="flex items-center border border-border rounded-md overflow-hidden">
                  {SIZE_OPTIONS.map(option => (
                    <button
                      key={option.value}
                      onClick={() => onResize(widget.id, option.value)}
                      disabled={widget.minSize && SIZE_OPTIONS.findIndex(s => s.value === option.value) < SIZE_OPTIONS.findIndex(s => s.value === widget.minSize)}
                      className={cn(
                        'px-2 py-1 text-xs transition-colors',
                        widget.size === option.value
                          ? 'bg-primary text-primary-foreground'
                          : 'hover:bg-muted',
                        'disabled:opacity-50 disabled:cursor-not-allowed'
                      )}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>

                {/* Visibility Toggle */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => onToggleVisibility(widget.id)}
                >
                  {widget.visible ? (
                    <Eye className="w-4 h-4" />
                  ) : (
                    <EyeOff className="w-4 h-4" />
                  )}
                </Button>
              </div>
            )}
          </CardTitle>
        </CardHeader>

        {/* Widget Content */}
        <CardContent className={cn(!widget.visible && 'opacity-50')}>
          {widget.component}
        </CardContent>
      </Card>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function DashboardGrid({
  widgets: initialWidgets,
  onLayoutChange,
  editable = true,
  className,
}: DashboardGridProps) {
  const [widgets, setWidgets] = useState<DashboardWidget[]>(initialWidgets);
  const [isEditing, setIsEditing] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  // Load saved layout from localStorage
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const savedLayout = JSON.parse(saved) as { id: string; size: DashboardWidget['size']; visible: boolean; order: number }[];
        
        // Merge saved layout with initial widgets
        const orderedWidgets = [...initialWidgets].sort((a, b) => {
          const aOrder = savedLayout.find(s => s.id === a.id)?.order ?? 999;
          const bOrder = savedLayout.find(s => s.id === b.id)?.order ?? 999;
          return aOrder - bOrder;
        }).map(widget => {
          const saved = savedLayout.find(s => s.id === widget.id);
          if (saved) {
            return { ...widget, size: saved.size, visible: saved.visible };
          }
          return widget;
        });

        setWidgets(orderedWidgets);
      } catch {
        // Invalid saved layout, use defaults
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Handle drag start
  const handleDragStart = useCallback((event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  }, []);

  // Handle drag end
  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (over && active.id !== over.id) {
      setWidgets(items => {
        const oldIndex = items.findIndex(i => i.id === active.id);
        const newIndex = items.findIndex(i => i.id === over.id);
        const newItems = arrayMove(items, oldIndex, newIndex);
        setHasChanges(true);
        return newItems;
      });
    }
  }, []);

  // Toggle widget visibility
  const handleToggleVisibility = useCallback((id: string) => {
    setWidgets(items =>
      items.map(item =>
        item.id === id ? { ...item, visible: !item.visible } : item
      )
    );
    setHasChanges(true);
  }, []);

  // Resize widget
  const handleResize = useCallback((id: string, size: DashboardWidget['size']) => {
    setWidgets(items =>
      items.map(item =>
        item.id === id ? { ...item, size } : item
      )
    );
    setHasChanges(true);
  }, []);

  // Save layout
  const handleSave = useCallback(() => {
    const layout = widgets.map((widget, index) => ({
      id: widget.id,
      size: widget.size,
      visible: widget.visible,
      order: index,
    }));

    localStorage.setItem(STORAGE_KEY, JSON.stringify(layout));
    onLayoutChange?.(widgets);
    setHasChanges(false);
    setIsEditing(false);
  }, [widgets, onLayoutChange]);

  // Reset to defaults
  const handleReset = useCallback(() => {
    setWidgets(initialWidgets);
    localStorage.removeItem(STORAGE_KEY);
    setHasChanges(false);
  }, [initialWidgets]);

  // Cancel editing
  const handleCancel = useCallback(() => {
    // Reload from storage or initial
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const savedLayout = JSON.parse(saved);
        const orderedWidgets = [...initialWidgets].sort((a, b) => {
          const aOrder = savedLayout.find((s: { id: string }) => s.id === a.id)?.order ?? 999;
          const bOrder = savedLayout.find((s: { id: string }) => s.id === b.id)?.order ?? 999;
          return aOrder - bOrder;
        }).map(widget => {
          const savedWidget = savedLayout.find((s: { id: string }) => s.id === widget.id);
          if (savedWidget) {
            return { ...widget, size: savedWidget.size, visible: savedWidget.visible };
          }
          return widget;
        });
        setWidgets(orderedWidgets);
      } catch {
        setWidgets(initialWidgets);
      }
    } else {
      setWidgets(initialWidgets);
    }
    setHasChanges(false);
    setIsEditing(false);
  }, [initialWidgets]);

  const activeWidget = activeId ? widgets.find(w => w.id === activeId) : null;

  return (
    <div className={className}>
      {/* Edit Mode Toolbar */}
      {editable && (
        <div className="flex items-center justify-end gap-2 mb-4">
          {isEditing ? (
            <>
              <Button variant="outline" size="sm" onClick={handleReset}>
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset
              </Button>
              <Button variant="outline" size="sm" onClick={handleCancel}>
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button size="sm" onClick={handleSave} disabled={!hasChanges}>
                <Save className="w-4 h-4 mr-2" />
                Save Layout
              </Button>
            </>
          ) : (
            <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
              <Settings2 className="w-4 h-4 mr-2" />
              Customize Dashboard
            </Button>
          )}
        </div>
      )}

      {/* Edit Mode Banner */}
      {isEditing && (
        <div className="mb-4 p-3 bg-primary/10 border border-primary/30 rounded-lg flex items-center gap-3">
          <Settings2 className="w-5 h-5 text-primary" />
          <div className="flex-1">
            <p className="text-sm font-medium">Customization Mode</p>
            <p className="text-xs text-muted-foreground">
              Drag widgets to reorder, resize with S/M/L/Full, or toggle visibility
            </p>
          </div>
          {hasChanges && (
            <div className="flex items-center gap-1 text-primary">
              <Check className="w-4 h-4" />
              <span className="text-xs">Unsaved changes</span>
            </div>
          )}
        </div>
      )}

      {/* Widget Grid */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={widgets.map(w => w.id)}
          strategy={rectSortingStrategy}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {widgets.map(widget => (
              <SortableWidget
                key={widget.id}
                widget={widget}
                isEditing={isEditing}
                onToggleVisibility={handleToggleVisibility}
                onResize={handleResize}
              />
            ))}
          </div>
        </SortableContext>

        {/* Drag Overlay */}
        <DragOverlay>
          {activeWidget && (
            <Card className="shadow-2xl ring-2 ring-primary opacity-90">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <GripVertical className="w-4 h-4" />
                  {activeWidget.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="opacity-50">
                {activeWidget.component}
              </CardContent>
            </Card>
          )}
        </DragOverlay>
      </DndContext>
    </div>
  );
}

export default DashboardGrid;

