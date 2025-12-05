'use client';

import { useDashboardStats } from '@/hooks/useAPI';
import { DataPage } from '@/components/page';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ModeToggle } from '@/components/mode/ModeToggle';
import { 
  TrendingUp, Calendar, AlertCircle, CheckCircle, Clock,
  Lightbulb, Settings, BarChart3, Zap, Activity
} from 'lucide-react';
import { formatRelativeTime } from '@/lib/utils';
import Link from 'next/link';
import { ROUTES } from '@/lib/constants';
import type { DashboardStats } from '@/types';

/**
 * Stat card configuration
 */
interface StatCard {
  label: string;
  value: number | string;
  change: string;
  icon: React.ElementType;
  color: string;
  href: string;
}

/**
 * Build stat cards from dashboard data
 */
function buildStatCards(stats: DashboardStats | null): StatCard[] {
  return [
    { 
      label: 'Total Releases', 
      value: stats?.total_releases || 0, 
      change: '+12%',
      icon: Calendar,
      color: 'text-blue-500',
      href: ROUTES.RELEASES
    },
    { 
      label: 'Active Agents', 
      value: stats?.active_agents || 0, 
      change: '+2',
      icon: Zap,
      color: 'text-green-500',
      href: ROUTES.METRICS
    },
    { 
      label: 'Feature Requests', 
      value: stats?.pending_requests || 0, 
      change: '+5',
      icon: Lightbulb,
      color: 'text-purple-500',
      href: ROUTES.FEATURE_REQUESTS
    },
    { 
      label: 'System Health', 
      value: `${stats?.system_health || 98}%`, 
      change: '+1%',
      icon: Activity,
      color: 'text-green-500',
      href: ROUTES.HEALTH
    },
  ];
}

/**
 * Stats Grid Component
 */
function StatsGrid({ stats }: { stats: DashboardStats }) {
  const statCards = buildStatCards(stats);
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((stat) => (
        <Link key={stat.label} href={stat.href}>
          <Card className="hover:shadow-lg transition-all hover:border-primary/50 cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground mb-1">
                {stat.value}
              </div>
              <p className="text-sm text-green-500 font-medium flex items-center gap-1">
                <TrendingUp size={14} />
                {stat.change}
              </p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

/**
 * Recent Activity Component
 */
function RecentActivity({ activities }: { activities: DashboardStats['recent_activity'] }) {
  const activityList = activities || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Recent Activity</span>
          <Badge variant="outline">{activityList.length} items</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activityList.length > 0 ? (
            activityList.slice(0, 6).map((activity, i) => (
              <div key={i} className="flex items-start gap-4 py-2 border-b border-border last:border-0">
                <div className="mt-1">
                  {activity.status === 'completed' ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : activity.status === 'in_progress' ? (
                    <Clock className="w-5 h-5 text-yellow-500 animate-spin" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-blue-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">
                    {activity.title}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {activity.description}
                  </p>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {formatRelativeTime(activity.timestamp)}
                </span>
              </div>
            ))
          ) : (
            <p className="text-muted-foreground text-center py-8">
              No recent activity
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Quick Actions Component
 */
function QuickActions() {
  const actions = [
    { label: 'Create New Release', icon: Calendar, href: ROUTES.RELEASES },
    { label: 'Submit Feature Request', icon: Lightbulb, href: ROUTES.FEATURE_REQUESTS },
    { label: 'View Metrics', icon: BarChart3, href: ROUTES.METRICS },
    { label: 'Configure System', icon: Settings, href: ROUTES.SETTINGS },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-3">
          {actions.map((action) => (
            <Link key={action.label} href={action.href}>
              <Button variant="outline" className="w-full justify-start" size="lg">
                <action.icon className="w-5 h-5 mr-3" />
                {action.label}
              </Button>
            </Link>
          ))}
        </div>
        
        <div className="mt-6 p-4 bg-primary/5 border border-primary/20 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Activity className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                All Systems Operational
              </p>
              <p className="text-xs text-muted-foreground">
                Last checked: {formatRelativeTime(new Date())}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Dashboard Content Component
 */
function DashboardContent({ stats }: { stats: DashboardStats }) {
  return (
    <div className="space-y-8">
      {/* Mode Toggle - Prominent Position */}
      <ModeToggle variant="card" />
      
      {/* Stats Grid */}
      <StatsGrid stats={stats} />
      
      {/* Activity and Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentActivity activities={stats.recent_activity} />
        <QuickActions />
      </div>
    </div>
  );
}

/**
 * Dashboard Page - Refactored to use DataPage
 */
export default function DashboardPage() {
  const { data: stats, error, isLoading, mutate } = useDashboardStats();

  return (
    <DataPage<DashboardStats>
      title="Dashboard"
      description="Welcome to your release automation command center"
      isLoading={isLoading}
      error={error}
      data={stats}
      onRetry={mutate}
      errorMessage="The backend API is not responding. Please check your connection."
      loadingLayout="cards"
      loadingCount={4}
    >
      {(dashboardStats) => <DashboardContent stats={dashboardStats} />}
    </DataPage>
  );
}
