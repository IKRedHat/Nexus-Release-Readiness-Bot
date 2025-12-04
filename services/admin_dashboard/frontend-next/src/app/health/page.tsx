'use client';

import { useHealthOverview } from '@/hooks/useAPI';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Layout from '@/components/Layout';
import { Activity, AlertCircle, CheckCircle, XCircle, RefreshCw, Clock } from 'lucide-react';
import { formatRelativeTime, formatPercentage, getStatusColor } from '@/lib/utils';
import type { HealthService } from '@/types';

export default function HealthPage() {
  const { data: health, error, isLoading, mutate } = useHealthOverview(10000); // Refresh every 10s

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-8">
          <Skeleton className="h-10 w-48" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-32" />)}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-48" />)}
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
              <h2 className="text-2xl font-bold mb-2">Unable to Load Health Data</h2>
              <p className="text-muted-foreground mb-6">
                Could not fetch system health from the backend API.
              </p>
              <Button onClick={() => mutate()}>Retry</Button>
            </div>
          </CardContent>
        </Card>
      </Layout>
    );
  }

  const services = health?.services || [];
  const healthyCount = services.filter((s: HealthService) => s.status === 'healthy').length;
  const degradedCount = services.filter((s: HealthService) => s.status === 'degraded').length;
  const downCount = services.filter((s: HealthService) => s.status === 'down').length;

  const getStatusIcon = (status: string) => {
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
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">
              System Health
            </h1>
            <p className="text-muted-foreground flex items-center gap-2">
              Last updated: {formatRelativeTime(health?.last_updated || new Date())}
              <Button 
                size="sm" 
                variant="ghost" 
                onClick={() => mutate()}
                className="ml-2"
              >
                <RefreshCw size={16} className="mr-1" />
                Refresh
              </Button>
            </p>
          </div>
          <Badge 
            className={getStatusColor(health?.overall_status || 'healthy')}
            variant="outline"
          >
            {health?.overall_status || 'Unknown'}
          </Badge>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="border-green-500/20">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-3xl font-bold text-green-500">{healthyCount}</p>
                  <p className="text-sm text-muted-foreground">Healthy Services</p>
                </div>
                <CheckCircle className="w-12 h-12 text-green-500/20" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-yellow-500/20">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-3xl font-bold text-yellow-500">{degradedCount}</p>
                  <p className="text-sm text-muted-foreground">Degraded Services</p>
                </div>
                <AlertCircle className="w-12 h-12 text-yellow-500/20" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-red-500/20">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-3xl font-bold text-red-500">{downCount}</p>
                  <p className="text-sm text-muted-foreground">Down Services</p>
                </div>
                <XCircle className="w-12 h-12 text-red-500/20" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Services Grid */}
        {services.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {services.map((service: HealthService) => (
              <Card 
                key={service.service} 
                className={`hover:shadow-lg transition-all ${
                  service.status === 'down' ? 'border-red-500/30' : 
                  service.status === 'degraded' ? 'border-yellow-500/30' : 
                  'border-green-500/20'
                }`}
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(service.status)}
                      <CardTitle className="text-lg">{service.service}</CardTitle>
                    </div>
                    <Badge className={getStatusColor(service.status)}>
                      {service.status}
                    </Badge>
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
                            <Badge key={i} variant="outline" className="text-xs">
                              {dep}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex gap-2 pt-2">
                      <Button size="sm" variant="outline" className="flex-1">
                        View Logs
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1">
                        <RefreshCw size={14} className="mr-1" />
                        Restart
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <Activity className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Services Monitored</h3>
                <p className="text-muted-foreground">
                  No health data available from the backend
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}

