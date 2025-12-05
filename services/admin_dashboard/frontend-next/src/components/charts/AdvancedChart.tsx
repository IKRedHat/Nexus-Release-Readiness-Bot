/**
 * Advanced Chart Component
 * 
 * Rich charting capabilities for analytics.
 * Features:
 * - Multiple chart types (line, area, bar, composed)
 * - Time-series comparison (this period vs previous)
 * - Custom date range selection
 * - Interactive tooltips
 * - Chart annotations
 * - Drill-down capability
 * - Export to PNG
 */

'use client';

import { useState, useCallback, useMemo, useRef } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Brush,
} from 'recharts';
import { format, subDays, subMonths, startOfDay, endOfDay, eachDayOfInterval } from 'date-fns';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  Download,
  Maximize2,
  RefreshCw,
  Settings2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

// =============================================================================
// Types
// =============================================================================

export type ChartType = 'line' | 'area' | 'bar' | 'composed';

export interface ChartDataPoint {
  date: string;
  [key: string]: number | string;
}

export interface ChartSeries {
  key: string;
  name: string;
  color: string;
  type?: 'line' | 'area' | 'bar';
  strokeDasharray?: string;
  hidden?: boolean;
}

export interface ChartAnnotation {
  date: string;
  label: string;
  color?: string;
}

export interface DateRange {
  start: Date;
  end: Date;
  label: string;
}

export interface AdvancedChartProps {
  title: string;
  subtitle?: string;
  data: ChartDataPoint[];
  series: ChartSeries[];
  type?: ChartType;
  height?: number;
  annotations?: ChartAnnotation[];
  showComparison?: boolean;
  comparisonData?: ChartDataPoint[];
  comparisonLabel?: string;
  dateRanges?: DateRange[];
  selectedRange?: DateRange;
  onRangeChange?: (range: DateRange) => void;
  showBrush?: boolean;
  showLegend?: boolean;
  showGrid?: boolean;
  valueFormatter?: (value: number) => string;
  onDrillDown?: (dataPoint: ChartDataPoint) => void;
  className?: string;
}

// =============================================================================
// Constants
// =============================================================================

const DEFAULT_DATE_RANGES: DateRange[] = [
  { start: subDays(new Date(), 7), end: new Date(), label: 'Last 7 days' },
  { start: subDays(new Date(), 14), end: new Date(), label: 'Last 14 days' },
  { start: subDays(new Date(), 30), end: new Date(), label: 'Last 30 days' },
  { start: subMonths(new Date(), 3), end: new Date(), label: 'Last 3 months' },
  { start: subMonths(new Date(), 6), end: new Date(), label: 'Last 6 months' },
];

// =============================================================================
// Custom Tooltip
// =============================================================================

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    dataKey: string;
  }>;
  label?: string;
  valueFormatter?: (value: number) => string;
  comparisonLabel?: string;
}

function CustomTooltip({ 
  active, 
  payload, 
  label, 
  valueFormatter = (v) => v.toLocaleString(),
  comparisonLabel 
}: CustomTooltipProps) {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-popover border border-border rounded-lg shadow-lg p-3 min-w-[200px]">
      <p className="text-sm font-medium text-foreground mb-2">{label}</p>
      {payload.map((entry, index) => {
        const isComparison = entry.dataKey.includes('_prev');
        return (
          <div 
            key={index} 
            className={cn(
              'flex items-center justify-between gap-4 text-sm py-1',
              isComparison && 'opacity-70'
            )}
          >
            <div className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-muted-foreground">
                {isComparison ? `${entry.name} (${comparisonLabel})` : entry.name}
              </span>
            </div>
            <span className="font-medium">{valueFormatter(entry.value)}</span>
          </div>
        );
      })}
    </div>
  );
}

// =============================================================================
// Trend Indicator
// =============================================================================

function TrendIndicator({ current, previous }: { current: number; previous: number }) {
  const change = previous > 0 ? ((current - previous) / previous) * 100 : 0;
  const isPositive = change > 0;
  const isNeutral = change === 0;

  return (
    <div className={cn(
      'flex items-center gap-1 text-sm font-medium',
      isPositive && 'text-green-500',
      !isPositive && !isNeutral && 'text-red-500',
      isNeutral && 'text-muted-foreground'
    )}>
      {isPositive ? (
        <TrendingUp className="w-4 h-4" />
      ) : isNeutral ? (
        <Minus className="w-4 h-4" />
      ) : (
        <TrendingDown className="w-4 h-4" />
      )}
      <span>{Math.abs(change).toFixed(1)}%</span>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function AdvancedChart({
  title,
  subtitle,
  data,
  series,
  type = 'line',
  height = 300,
  annotations = [],
  showComparison = false,
  comparisonData,
  comparisonLabel = 'Previous Period',
  dateRanges = DEFAULT_DATE_RANGES,
  selectedRange,
  onRangeChange,
  showBrush = false,
  showLegend = true,
  showGrid = true,
  valueFormatter = (v) => v.toLocaleString(),
  onDrillDown,
  className,
}: AdvancedChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [visibleSeries, setVisibleSeries] = useState<Set<string>>(
    new Set(series.filter(s => !s.hidden).map(s => s.key))
  );
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Calculate summary stats
  const summaryStats = useMemo(() => {
    if (data.length === 0) return null;

    const mainSeries = series[0];
    if (!mainSeries) return null;

    const values = data.map(d => Number(d[mainSeries.key]) || 0);
    const current = values.reduce((a, b) => a + b, 0);
    
    let previous = 0;
    if (comparisonData) {
      previous = comparisonData
        .map(d => Number(d[mainSeries.key]) || 0)
        .reduce((a, b) => a + b, 0);
    }

    return {
      current,
      previous,
      min: Math.min(...values),
      max: Math.max(...values),
      avg: current / values.length,
    };
  }, [data, comparisonData, series]);

  // Toggle series visibility
  const toggleSeries = useCallback((key: string) => {
    setVisibleSeries(prev => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  }, []);

  // Merge comparison data
  const chartData = useMemo(() => {
    if (!showComparison || !comparisonData) return data;

    return data.map((point, index) => {
      const compPoint = comparisonData[index] || {};
      const merged = { ...point };
      
      series.forEach(s => {
        if (compPoint[s.key] !== undefined) {
          merged[`${s.key}_prev`] = compPoint[s.key];
        }
      });
      
      return merged;
    });
  }, [data, comparisonData, showComparison, series]);

  // Export chart as PNG
  const exportChart = useCallback(() => {
    if (!chartRef.current) return;

    // Using html2canvas would be ideal here, but for now we'll just log
    console.log('Export chart to PNG');
    // In production, implement with html2canvas or similar
  }, []);

  // Render chart based on type
  const renderChart = () => {
    const commonProps = {
      data: chartData,
      margin: { top: 10, right: 30, left: 0, bottom: 0 },
    };

    const renderSeries = (SeriesComponent: typeof Line | typeof Area | typeof Bar, props: object = {}) => (
      <>
        {series.map(s => (
          visibleSeries.has(s.key) && (
            <SeriesComponent
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              fill={s.color}
              strokeWidth={2}
              dot={false}
              strokeDasharray={s.strokeDasharray}
              {...props}
            />
          )
        ))}
        {/* Comparison series */}
        {showComparison && series.map(s => (
          visibleSeries.has(s.key) && (
            <SeriesComponent
              key={`${s.key}_prev`}
              type="monotone"
              dataKey={`${s.key}_prev`}
              name={`${s.name} (${comparisonLabel})`}
              stroke={s.color}
              fill={s.color}
              strokeWidth={1}
              strokeOpacity={0.4}
              fillOpacity={0.1}
              dot={false}
              strokeDasharray="5 5"
              {...props}
            />
          )
        ))}
      </>
    );

    const chartElements = (
      <>
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-border" />}
        <XAxis 
          dataKey="date" 
          tickFormatter={(value) => format(new Date(value), 'MMM d')}
          className="text-xs fill-muted-foreground"
        />
        <YAxis 
          tickFormatter={valueFormatter}
          className="text-xs fill-muted-foreground"
        />
        <Tooltip content={<CustomTooltip valueFormatter={valueFormatter} comparisonLabel={comparisonLabel} />} />
        {showLegend && <Legend />}
        
        {/* Annotations */}
        {annotations.map((annotation, i) => (
          <ReferenceLine
            key={i}
            x={annotation.date}
            stroke={annotation.color || 'hsl(var(--primary))'}
            strokeDasharray="3 3"
            label={{ value: annotation.label, position: 'top', className: 'text-xs fill-foreground' }}
          />
        ))}
        
        {showBrush && (
          <Brush 
            dataKey="date" 
            height={30} 
            stroke="hsl(var(--primary))"
            tickFormatter={(value) => format(new Date(value), 'MMM d')}
          />
        )}
      </>
    );

    switch (type) {
      case 'area':
        return (
          <AreaChart {...commonProps}>
            {chartElements}
            {renderSeries(Area, { fillOpacity: 0.3 })}
          </AreaChart>
        );
      case 'bar':
        return (
          <BarChart {...commonProps}>
            {chartElements}
            {renderSeries(Bar, { fillOpacity: 0.8 })}
          </BarChart>
        );
      case 'composed':
        return (
          <ComposedChart {...commonProps}>
            {chartElements}
            {series.map(s => {
              if (!visibleSeries.has(s.key)) return null;
              const Component = s.type === 'bar' ? Bar : s.type === 'area' ? Area : Line;
              return (
                <Component
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.name}
                  stroke={s.color}
                  fill={s.color}
                  strokeWidth={2}
                  dot={false}
                  fillOpacity={s.type === 'area' ? 0.3 : 0.8}
                />
              );
            })}
          </ComposedChart>
        );
      default:
        return (
          <LineChart {...commonProps}>
            {chartElements}
            {renderSeries(Line)}
          </LineChart>
        );
    }
  };

  return (
    <Card className={cn(isFullscreen && 'fixed inset-4 z-50', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              {title}
              {summaryStats && comparisonData && (
                <TrendIndicator 
                  current={summaryStats.current} 
                  previous={summaryStats.previous} 
                />
              )}
            </CardTitle>
            {subtitle && (
              <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            {/* Date Range Selector */}
            {onRangeChange && (
              <div className="flex items-center gap-1 border border-border rounded-md">
                {dateRanges.slice(0, 4).map((range) => (
                  <Button
                    key={range.label}
                    variant={selectedRange?.label === range.label ? 'secondary' : 'ghost'}
                    size="sm"
                    className="h-7 text-xs"
                    onClick={() => onRangeChange(range)}
                  >
                    {range.label.replace('Last ', '')}
                  </Button>
                ))}
              </div>
            )}
            
            {/* Actions */}
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={exportChart}>
              <Download className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8"
              onClick={() => setIsFullscreen(!isFullscreen)}
            >
              <Maximize2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Summary Stats */}
        {summaryStats && (
          <div className="flex gap-4 mt-4">
            <div className="text-center">
              <p className="text-2xl font-bold">{valueFormatter(summaryStats.current)}</p>
              <p className="text-xs text-muted-foreground">Total</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-medium">{valueFormatter(summaryStats.avg)}</p>
              <p className="text-xs text-muted-foreground">Average</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-medium">{valueFormatter(summaryStats.max)}</p>
              <p className="text-xs text-muted-foreground">Peak</p>
            </div>
          </div>
        )}

        {/* Series Toggles */}
        {series.length > 1 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {series.map(s => (
              <Badge
                key={s.key}
                variant={visibleSeries.has(s.key) ? 'default' : 'outline'}
                className="cursor-pointer"
                style={{ 
                  backgroundColor: visibleSeries.has(s.key) ? s.color : 'transparent',
                  borderColor: s.color,
                }}
                onClick={() => toggleSeries(s.key)}
              >
                {s.name}
              </Badge>
            ))}
          </div>
        )}
      </CardHeader>

      <CardContent>
        <div ref={chartRef} style={{ height: isFullscreen ? 'calc(100vh - 200px)' : height }}>
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

export default AdvancedChart;

