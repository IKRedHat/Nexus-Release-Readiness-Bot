'use client';

import { useHealthOverview } from '@/hooks/useAPI';
import { DataPage } from '@/components/page';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, AlertCircle, CheckCircle, XCircle, RefreshCw, Clock } from 'lucide-react';
import { formatRelativeTime, formatPercentage, getStatusColor } from '@/lib/utils';
import type { HealthService, HealthOverview } from '@/types';

/**
 * Get status icon for service
 */
function getStatusIcon(status: string) {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="w-6 h-6 text-green-500" />;
    case 'degraded':
      return <AlertCircle className="w-6 h-6 text-yellow-500" />;
    case 'down':
      return <XCircle className="w-6 h-6 text-red-500" />;
    default:
      return <Activity className="w-6 h-6 text-gray-500" />;
  }
}

/**
 * Empty state component
 */
function EmptyHealth() {
  return (
    <Card>
      <CardContent className="py-12">
        <div className="text-center">
          <Activity className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">No Services Monitored</h3>
          <p className="text-muted-foreground">No health data available from the backend</p>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Health stats cards
 */
function HealthStats({ services }: { services: HealthService[] }) {
  const healthyCount = services.filter(s => s.status === 'healthy').length;
  const degradedCount = services.filter(s => s.status === 'degraded').length;
  const downCount = services.filter(s => s.status === 'down').length;

  const stats = [
    { label: 'Healthy Services', value: healthyCount, color: 'text-green-500', icon: CheckCircle, borderColor: 'border-green-500/20' },
    { label: 'Degraded Services', value: degradedCount, color: 'text-yellow-500', icon: AlertCircle, borderColor: 'border-yellow-500/20' },
    { label: 'Down Services', value: downCount, color: 'text-red-500', icon: XCircle, borderColor: 'border-red-500/20' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {stats.map(stat => {
        const Icon = stat.icon;
        return (
          <Card key={stat.label} className={stat.borderColor}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                </div>
                <Icon className={`w-12 h-12 ${stat.color} opacity-20`} />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

/**
 * Single service card
 */
function ServiceCard({ service }: { service: HealthService }) {
  const borderColor = 
    service.status === 'down' ? 'border-red-500/30' : 
    service.status === 'degraded' ? 'border-yellow-500/30' : 
    'border-green-500/20';

  return (
    <Card className={`hover:shadow-lg transition-all ${borderColor}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getStatusIcon(service.status)}
            <CardTitle className="text-lg">{service.service}</CardTitle>
          </div>
          <Badge className={getStatusColor(service.status)}>{service.status}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Uptime</p>
              <p className="text-sm font-semibold text-foreground">
                {formatPercentage(service.uptime_percentage || 0, 2)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Response Time</p>
              <p className="text-sm font-semibold text-foreground">
                {service.response_time ? `${service.response_time}ms` : 'N/A'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground pt-2 border-t border-border">
            <Clock size={14} />
            Last check: {formatRelativeTime(service.last_check)}
          </div>

          {service.error_message && (
            <div className="p-2 bg-destructive/10 border border-destructive/20 rounded text-xs text-destructive">
              {service.error_message}
            </div>
          )}

          {service.dependencies && service.dependencies.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Dependencies:</p>
              <div className="flex flex-wrap gap-1">
                {service.dependencies.map((dep, i) => (
                  <Badge key={i} variant="outline" className="text-xs">{dep}</Badge>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <Button size="sm" variant="outline" className="flex-1">View Logs</Button>
            <Button size="sm" variant="outline" className="flex-1">
              <RefreshCw size={14} className="mr-1" />
              Restart
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Health page - refactored to use DataPage
 */
export default function HealthPage() {
  const { data: health, error, isLoading, mutate } = useHealthOverview(10000);

  const headerActions = health && (
    <div className="flex items-center gap-3">
      <Badge className={getStatusColor(health?.overall_status || 'healthy')} variant="outline">
        {health?.overall_status || 'Unknown'}
      </Badge>
      <Button size="sm" variant="ghost" onClick={() => mutate()}>
        <RefreshCw size={16} className="mr-1" />
        Refresh
      </Button>
    </div>
  );

  const description = health
    ? `Last updated: ${formatRelativeTime(health.last_updated || new Date())}`
    : 'Monitor the health and status of all services';

  return (
    <DataPage<HealthOverview>
      title="System Health"
      description={description}
      isLoading={isLoading}
      error={error}
      data={health}
      onRetry={mutate}
      errorMessage="Could not fetch system health from the backend API."
      loadingLayout="grid"
      loadingCount={4}
      emptyState={<EmptyHealth />}
      actions={headerActions}
    >
      {(healthData) => {
        const services = healthData?.services || [];
        
        return (
          <div className="space-y-6">
            <HealthStats services={services} />
            
            {services.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {services.map((service: HealthService) => (
                  <ServiceCard key={service.service} service={service} />
                ))}
              </div>
            ) : (
              <EmptyHealth />
            )}
          </div>
        );
      }}
    </DataPage>
  );
}
