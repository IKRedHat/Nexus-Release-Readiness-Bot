/**
 * Release Timeline / Gantt View Component
 * 
 * An interactive timeline view for release planning.
 * Features:
 * - Horizontal scrolling timeline
 * - Release bars with duration
 * - Status color coding
 * - Today marker
 * - Zoom levels (day/week/month)
 * - Click to edit
 * - Hover tooltips
 */

'use client';

import { useState, useMemo, useRef, useEffect } from 'react';
import { 
  format, 
  startOfMonth, 
  endOfMonth, 
  eachDayOfInterval, 
  eachWeekOfInterval,
  addMonths, 
  subMonths, 
  isToday, 
  differenceInDays,
  parseISO,
  isSameMonth,
  startOfWeek,
  endOfWeek,
  addDays,
} from 'date-fns';
import { 
  ChevronLeft, 
  ChevronRight, 
  ZoomIn, 
  ZoomOut, 
  Calendar,
  LayoutGrid,
  LayoutList,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Release } from '@/types';

// =============================================================================
// Types
// =============================================================================

type ZoomLevel = 'day' | 'week' | 'month';
type ViewMode = 'timeline' | 'grid';

interface ReleaseTimelineProps {
  releases: Release[];
  onReleaseClick?: (release: Release) => void;
  className?: string;
}

interface TimelineRelease extends Release {
  startDate: Date;
  endDate: Date;
  left: number;
  width: number;
}

// =============================================================================
// Constants
// =============================================================================

const STATUS_COLORS: Record<string, string> = {
  planned: 'bg-purple-500',
  in_progress: 'bg-blue-500',
  completed: 'bg-green-500',
  cancelled: 'bg-gray-500',
};

const STATUS_BG_LIGHT: Record<string, string> = {
  planned: 'bg-purple-500/20 border-purple-500/50',
  in_progress: 'bg-blue-500/20 border-blue-500/50',
  completed: 'bg-green-500/20 border-green-500/50',
  cancelled: 'bg-gray-500/20 border-gray-500/50',
};

const CELL_WIDTHS: Record<ZoomLevel, number> = {
  day: 40,
  week: 100,
  month: 150,
};

// =============================================================================
// Component
// =============================================================================

export function ReleaseTimeline({ 
  releases, 
  onReleaseClick,
  className 
}: ReleaseTimelineProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [zoomLevel, setZoomLevel] = useState<ZoomLevel>('week');
  const [viewMode, setViewMode] = useState<ViewMode>('timeline');
  const [hoveredRelease, setHoveredRelease] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  // Calculate timeline range
  const timelineRange = useMemo(() => {
    const start = subMonths(startOfMonth(currentDate), 1);
    const end = addMonths(endOfMonth(currentDate), 2);
    return { start, end };
  }, [currentDate]);

  // Generate timeline columns
  const columns = useMemo(() => {
    const { start, end } = timelineRange;
    
    switch (zoomLevel) {
      case 'day':
        return eachDayOfInterval({ start, end }).map(date => ({
          date,
          label: format(date, 'd'),
          header: format(date, 'EEE'),
          isToday: isToday(date),
          isWeekend: date.getDay() === 0 || date.getDay() === 6,
        }));
      case 'week':
        return eachWeekOfInterval({ start, end }).map(date => ({
          date,
          label: format(date, 'MMM d'),
          header: `Week ${format(date, 'w')}`,
          isToday: false,
          isWeekend: false,
        }));
      case 'month':
        const months = [];
        let current = start;
        while (current <= end) {
          months.push({
            date: current,
            label: format(current, 'MMMM'),
            header: format(current, 'yyyy'),
            isToday: false,
            isWeekend: false,
          });
          current = addMonths(current, 1);
        }
        return months;
    }
  }, [timelineRange, zoomLevel]);

  // Calculate release positions
  const timelineReleases: TimelineRelease[] = useMemo(() => {
    const { start, end } = timelineRange;
    const totalDays = differenceInDays(end, start);
    const totalWidth = columns.length * CELL_WIDTHS[zoomLevel];

    return releases.map(release => {
      const releaseDate = parseISO(release.release_date);
      const startDate = subMonths(releaseDate, 0); // Could add planning phase duration
      const endDate = releaseDate;
      
      const startOffset = Math.max(0, differenceInDays(startDate, start));
      const duration = Math.max(1, differenceInDays(endDate, startDate) + 1);
      
      const left = (startOffset / totalDays) * totalWidth;
      const width = Math.max(80, (duration / totalDays) * totalWidth);

      return {
        ...release,
        startDate,
        endDate,
        left,
        width,
      };
    });
  }, [releases, timelineRange, columns.length, zoomLevel]);

  // Scroll to today on mount
  useEffect(() => {
    if (timelineRef.current) {
      const todayIndex = columns.findIndex(col => isToday(col.date));
      if (todayIndex > -1) {
        const scrollPosition = todayIndex * CELL_WIDTHS[zoomLevel] - 200;
        timelineRef.current.scrollLeft = Math.max(0, scrollPosition);
      }
    }
  }, [columns, zoomLevel]);

  // Navigation
  const navigatePrev = () => setCurrentDate(prev => subMonths(prev, 1));
  const navigateNext = () => setCurrentDate(prev => addMonths(prev, 1));
  const navigateToday = () => setCurrentDate(new Date());

  // Zoom
  const zoomIn = () => {
    if (zoomLevel === 'month') setZoomLevel('week');
    else if (zoomLevel === 'week') setZoomLevel('day');
  };
  
  const zoomOut = () => {
    if (zoomLevel === 'day') setZoomLevel('week');
    else if (zoomLevel === 'week') setZoomLevel('month');
  };

  const cellWidth = CELL_WIDTHS[zoomLevel];

  return (
    <div className={cn('border border-border rounded-lg overflow-hidden bg-card', className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/50">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={navigatePrev}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={navigateToday}>
            Today
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={navigateNext}>
            <ChevronRight className="h-4 w-4" />
          </Button>
          <span className="text-sm font-medium ml-2">
            {format(currentDate, 'MMMM yyyy')}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center border border-border rounded-md">
            <Button
              variant={viewMode === 'timeline' ? 'secondary' : 'ghost'}
              size="sm"
              className="h-8 rounded-r-none"
              onClick={() => setViewMode('timeline')}
            >
              <LayoutList className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
              size="sm"
              className="h-8 rounded-l-none"
              onClick={() => setViewMode('grid')}
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
          </div>

          {/* Zoom Controls */}
          <div className="flex items-center border border-border rounded-md">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-r-none"
              onClick={zoomOut}
              disabled={zoomLevel === 'month'}
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <span className="px-2 text-xs text-muted-foreground border-x border-border">
              {zoomLevel}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-l-none"
              onClick={zoomIn}
              disabled={zoomLevel === 'day'}
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <div ref={containerRef} className="relative">
          {/* Header Row */}
          <div 
            ref={timelineRef}
            className="overflow-x-auto"
          >
            <div 
              className="relative"
              style={{ width: columns.length * cellWidth }}
            >
              {/* Column Headers */}
              <div className="flex border-b border-border bg-muted/30 sticky top-0 z-10">
                {columns.map((col, i) => (
                  <div
                    key={i}
                    className={cn(
                      'flex-shrink-0 border-r border-border px-1 py-2 text-center',
                      col.isToday && 'bg-primary/10',
                      col.isWeekend && 'bg-muted/50'
                    )}
                    style={{ width: cellWidth }}
                  >
                    <div className="text-xs text-muted-foreground">{col.header}</div>
                    <div className={cn(
                      'text-sm font-medium',
                      col.isToday && 'text-primary'
                    )}>
                      {col.label}
                    </div>
                  </div>
                ))}
              </div>

              {/* Release Rows */}
              <div className="relative min-h-[200px]">
                {/* Today Line */}
                {columns.some(col => col.isToday) && (
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-20"
                    style={{
                      left: columns.findIndex(col => col.isToday) * cellWidth + cellWidth / 2,
                    }}
                  />
                )}

                {/* Grid Lines */}
                <div className="absolute inset-0 flex">
                  {columns.map((col, i) => (
                    <div
                      key={i}
                      className={cn(
                        'flex-shrink-0 border-r border-border/50',
                        col.isWeekend && 'bg-muted/30'
                      )}
                      style={{ width: cellWidth }}
                    />
                  ))}
                </div>

                {/* Release Bars */}
                {timelineReleases.map((release, index) => (
                  <div
                    key={release.id}
                    className={cn(
                      'absolute h-10 rounded-md border cursor-pointer transition-all',
                      STATUS_BG_LIGHT[release.status],
                      hoveredRelease === release.id && 'shadow-lg scale-[1.02] z-10'
                    )}
                    style={{
                      left: release.left,
                      width: release.width,
                      top: index * 48 + 8,
                    }}
                    onClick={() => onReleaseClick?.(release)}
                    onMouseEnter={() => setHoveredRelease(release.id)}
                    onMouseLeave={() => setHoveredRelease(null)}
                  >
                    <div className="flex items-center h-full px-3 gap-2 overflow-hidden">
                      <div className={cn('w-2 h-2 rounded-full flex-shrink-0', STATUS_COLORS[release.status])} />
                      <span className="text-sm font-medium truncate">{release.version}</span>
                      <span className="text-xs text-muted-foreground truncate hidden sm:block">
                        {release.name}
                      </span>
                    </div>

                    {/* Tooltip */}
                    {hoveredRelease === release.id && (
                      <div className="absolute left-0 top-full mt-2 z-30 p-3 bg-popover border border-border rounded-lg shadow-lg min-w-[200px]">
                        <div className="font-medium">{release.version}</div>
                        <div className="text-sm text-muted-foreground">{release.name}</div>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge className={cn('text-xs', STATUS_COLORS[release.status])}>
                            {release.status.replace('_', ' ')}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {format(parseISO(release.release_date), 'MMM d, yyyy')}
                          </span>
                        </div>
                        {release.description && (
                          <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                            {release.description}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Grid View (Compact Calendar) */}
      {viewMode === 'grid' && (
        <div className="p-4">
          <div className="grid grid-cols-7 gap-1">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center text-xs text-muted-foreground py-2">
                {day}
              </div>
            ))}
            {eachDayOfInterval({
              start: startOfWeek(startOfMonth(currentDate)),
              end: endOfWeek(endOfMonth(currentDate)),
            }).map(day => {
              const dayReleases = timelineReleases.filter(r => 
                format(r.endDate, 'yyyy-MM-dd') === format(day, 'yyyy-MM-dd')
              );
              
              return (
                <div
                  key={day.toISOString()}
                  className={cn(
                    'min-h-[80px] p-1 border border-border rounded',
                    !isSameMonth(day, currentDate) && 'opacity-50',
                    isToday(day) && 'bg-primary/10 border-primary'
                  )}
                >
                  <div className={cn(
                    'text-sm mb-1',
                    isToday(day) ? 'font-bold text-primary' : 'text-muted-foreground'
                  )}>
                    {format(day, 'd')}
                  </div>
                  {dayReleases.slice(0, 2).map(release => (
                    <div
                      key={release.id}
                      className={cn(
                        'text-xs p-1 rounded mb-1 cursor-pointer truncate',
                        STATUS_BG_LIGHT[release.status]
                      )}
                      onClick={() => onReleaseClick?.(release)}
                    >
                      {release.version}
                    </div>
                  ))}
                  {dayReleases.length > 2 && (
                    <div className="text-xs text-muted-foreground">
                      +{dayReleases.length - 2} more
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 px-4 py-2 border-t border-border bg-muted/30">
        {Object.entries(STATUS_COLORS).map(([status, color]) => (
          <div key={status} className="flex items-center gap-1.5">
            <div className={cn('w-3 h-3 rounded', color)} />
            <span className="text-xs text-muted-foreground capitalize">
              {status.replace('_', ' ')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ReleaseTimeline;

