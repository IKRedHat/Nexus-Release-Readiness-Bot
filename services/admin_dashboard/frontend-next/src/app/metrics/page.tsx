'use client';

import { useMetrics, useSystemMetrics } from '@/hooks/useAPI';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import Layout from '@/components/Layout';
import { BarChart3, AlertCircle, TrendingUp, Cpu, HardDrive, Network } from 'lucide-react';
import { formatNumber, formatBytes } from '@/lib/utils';
import type { AgentMetrics, SystemMetrics } from '@/types';

export default function MetricsPage() {
  const { data: agents, error: agentsError, isLoading: agentsLoading } = useMetrics();
  const { data: system, error: systemError, isLoading: systemLoading } = useSystemMetrics();

  const isLoading = agentsLoading || systemLoading;
  const error = agentsError || systemError;

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-8">
          <Skeleton className="h-10 w-48" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32" />)}
          </div>
          <Skeleton className="h-96" />
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
              <h2 className="text-2xl font-bold mb-2">Unable to Load Metrics</h2>
              <p className="text-muted-foreground mb-6">
                Could not fetch metrics data from the backend API.
              </p>
              <Button onClick={() => window.location.reload()}>Retry</Button>
            </div>
          </CardContent>
        </Card>
      </Layout>
    );
  }

  const agentsList = agents || [];
  const systemMetrics: SystemMetrics = system || {
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    network_in: 0,
    network_out: 0,
    active_connections: 0,
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Metrics & Observability
          </h1>
          <p className="text-muted-foreground">
            Monitor system performance and agent metrics
          </p>
        </div>

        {/* System Metrics */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">System Resources</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <Cpu className="w-8 h-8 text-blue-500" />
                  <span className="text-3xl font-bold">{systemMetrics.cpu_usage}%</span>
                </div>
                <p className="text-sm text-muted-foreground">CPU Usage</p>
                <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 transition-all" 
                    style={{ width: `${systemMetrics.cpu_usage}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <HardDrive className="w-8 h-8 text-purple-500" />
                  <span className="text-3xl font-bold">{systemMetrics.memory_usage}%</span>
                </div>
                <p className="text-sm text-muted-foreground">Memory Usage</p>
                <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-purple-500 transition-all" 
                    style={{ width: `${systemMetrics.memory_usage}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <HardDrive className="w-8 h-8 text-orange-500" />
                  <span className="text-3xl font-bold">{systemMetrics.disk_usage}%</span>
                </div>
                <p className="text-sm text-muted-foreground">Disk Usage</p>
                <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-orange-500 transition-all" 
                    style={{ width: `${systemMetrics.disk_usage}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <Network className="w-8 h-8 text-green-500" />
                  <span className="text-3xl font-bold">{systemMetrics.active_connections}</span>
                </div>
                <p className="text-sm text-muted-foreground">Active Connections</p>
                <div className="mt-2 text-xs text-muted-foreground">
                  ↓ {formatBytes(systemMetrics.network_in)} | ↑ {formatBytes(systemMetrics.network_out)}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Agent Metrics */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">Agent Performance</h2>
          {agentsList.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {agentsList.map((agent: AgentMetrics) => {
                const successRate = agent.requests_total > 0 
                  ? (agent.requests_success / agent.requests_total) * 100
                  : 0;

                return (
                  <Card key={agent.agent_name} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>{agent.agent_name}</span>
                        <div className="flex items-center gap-1 text-sm font-normal">
                          <TrendingUp size={16} className="text-green-500" />
                          <span className="text-green-500">{successRate.toFixed(1)}%</span>
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="grid grid-cols-3 gap-4">
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">Total Requests</p>
                            <p className="text-2xl font-bold text-foreground">
                              {formatNumber(agent.requests_total)}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">Success</p>
                            <p className="text-2xl font-bold text-green-500">
                              {formatNumber(agent.requests_success)}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">Failed</p>
                            <p className="text-2xl font-bold text-red-500">
                              {formatNumber(agent.requests_failed)}
                            </p>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">Avg Response Time</p>
                            <p className="text-lg font-semibold text-foreground">
                              {agent.avg_response_time}ms
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">Uptime</p>
                            <p className="text-lg font-semibold text-foreground">
                              {agent.uptime.toFixed(2)}%
                            </p>
                          </div>
                        </div>

                        <div className="text-xs text-muted-foreground">
                          Last activity: {agent.last_activity}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center">
                  <BarChart3 className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">No Agent Metrics</h3>
                  <p className="text-muted-foreground">
                    No agent performance data available
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </Layout>
  );
}

