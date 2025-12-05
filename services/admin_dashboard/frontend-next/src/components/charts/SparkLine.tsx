/**
 * SparkLine Component
 * 
 * Compact inline charts for trend visualization.
 * Perfect for tables and stat cards.
 */

'use client';

import { useMemo } from 'react';
import { LineChart, Line, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { cn } from '@/lib/utils';

// =============================================================================
// Types
// =============================================================================

export interface SparkLineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  type?: 'line' | 'area';
  showDot?: boolean;
  className?: string;
}

// =============================================================================
// Component
// =============================================================================

export function SparkLine({
  data,
  width = 100,
  height = 32,
  color = 'hsl(var(--primary))',
  type = 'line',
  showDot = true,
  className,
}: SparkLineProps) {
  const chartData = useMemo(() => 
    data.map((value, index) => ({ value, index })),
    [data]
  );

  const trend = useMemo(() => {
    if (data.length < 2) return 'neutral';
    const first = data[0];
    const last = data[data.length - 1];
    if (last > first) return 'up';
    if (last < first) return 'down';
    return 'neutral';
  }, [data]);

  const trendColor = trend === 'up' 
    ? 'hsl(142.1 76.2% 36.3%)' // green
    : trend === 'down' 
      ? 'hsl(0 84.2% 60.2%)' // red
      : color;

  if (type === 'area') {
    return (
      <div className={cn('inline-block', className)} style={{ width, height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
            <defs>
              <linearGradient id={`sparkline-gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={trendColor} stopOpacity={0.3} />
                <stop offset="100%" stopColor={trendColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey="value"
              stroke={trendColor}
              strokeWidth={1.5}
              fill={`url(#sparkline-gradient-${color})`}
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className={cn('inline-block', className)} style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={trendColor}
            strokeWidth={1.5}
            dot={showDot ? {
              r: 0,
              fill: trendColor,
            } : false}
            activeDot={showDot ? {
              r: 3,
              fill: trendColor,
            } : false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// =============================================================================
// SparkBar Component
// =============================================================================

export interface SparkBarProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  className?: string;
}

export function SparkBar({
  data,
  width = 100,
  height = 32,
  color = 'hsl(var(--primary))',
  className,
}: SparkBarProps) {
  const max = Math.max(...data, 1);
  
  return (
    <div 
      className={cn('inline-flex items-end gap-[2px]', className)} 
      style={{ width, height }}
    >
      {data.map((value, i) => (
        <div
          key={i}
          className="flex-1 rounded-t"
          style={{
            height: `${(value / max) * 100}%`,
            backgroundColor: color,
            opacity: 0.3 + (i / data.length) * 0.7,
            minHeight: 2,
          }}
        />
      ))}
    </div>
  );
}

// =============================================================================
// Trend Badge
// =============================================================================

export interface TrendBadgeProps {
  value: number;
  previousValue: number;
  format?: 'percent' | 'absolute';
  showSparkline?: boolean;
  sparklineData?: number[];
  className?: string;
}

export function TrendBadge({
  value,
  previousValue,
  format = 'percent',
  showSparkline = false,
  sparklineData,
  className,
}: TrendBadgeProps) {
  const change = previousValue > 0 
    ? ((value - previousValue) / previousValue) * 100 
    : 0;
  
  const isPositive = change > 0;
  const isNegative = change < 0;

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {showSparkline && sparklineData && (
        <SparkLine data={sparklineData} width={60} height={20} />
      )}
      <span className={cn(
        'text-sm font-medium',
        isPositive && 'text-green-500',
        isNegative && 'text-red-500',
        !isPositive && !isNegative && 'text-muted-foreground'
      )}>
        {isPositive ? '↑' : isNegative ? '↓' : '→'}
        {format === 'percent' 
          ? `${Math.abs(change).toFixed(1)}%`
          : Math.abs(value - previousValue).toLocaleString()
        }
      </span>
    </div>
  );
}

export default SparkLine;

