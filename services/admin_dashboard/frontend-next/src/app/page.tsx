'use client';

import { useDashboardStats } from '@/hooks/useAPI';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Layout from '@/components/Layout';
import { 
  TrendingUp, Users, Zap, Activity, Calendar, AlertCircle, CheckCircle, Clock,
  Lightbulb, Settings, BarChart3
} from 'lucide-react';
import { formatRelativeTime, getStatusColor } from '@/lib/utils';
import Link from 'next/link';
import { ROUTES } from '@/lib/constants';

export default function DashboardPage() {
  const { data: stats, error, isLoading } = useDashboardStats();

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-8">
          <div>
            <Skeleton className="h-10 w-64 mb-2" />
            <Skeleton className="h-6 w-96" />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Skeleton className="h-96" />
            <Skeleton className="h-96" />
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <Card className="max-w-2xl mx-auto mt-20">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="w-16 h-16 text-destructive mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-foreground mb-2">
                Unable to Load Dashboard
              </h2>
              <p className="text-muted-foreground mb-6">
                The backend API is not responding. Please check your connection.
              </p>
              <Button onClick={() => window.location.reload()}>
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </Layout>
    );
  }

  const statCards = [
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

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Dashboard
          </h1>
          <p className="text-muted-foreground text-lg">
            Welcome to your release automation command center
          </p>
        </div>
        
        {/* Stats Grid */}
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
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Recent Activity</span>
                <Badge variant="outline">{stats?.recent_activity?.length || 0} items</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats?.recent_activity?.slice(0, 6).map((activity: any, i: number) => (
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
                )) || (
                  <p className="text-muted-foreground text-center py-8">
                    No recent activity
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
          
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-3">
                <Link href={ROUTES.RELEASES}>
                  <Button variant="outline" className="w-full justify-start" size="lg">
                    <Calendar className="w-5 h-5 mr-3" />
                    Create New Release
                  </Button>
                </Link>
                <Link href={ROUTES.FEATURE_REQUESTS}>
                  <Button variant="outline" className="w-full justify-start" size="lg">
                    <Lightbulb className="w-5 h-5 mr-3" />
                    Submit Feature Request
                  </Button>
                </Link>
                <Link href={ROUTES.METRICS}>
                  <Button variant="outline" className="w-full justify-start" size="lg">
                    <BarChart3 className="w-5 h-5 mr-3" />
                    View Metrics
                  </Button>
                </Link>
                <Link href={ROUTES.SETTINGS}>
                  <Button variant="outline" className="w-full justify-start" size="lg">
                    <Settings className="w-5 h-5 mr-3" />
                    Configure System
                  </Button>
                </Link>
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
        </div>
      </div>
    </Layout>
  );
}
