'use client';

import { useMetrics, useSystemMetrics } from '@/hooks/useAPI';
import { DataPage } from '@/components/page';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3, TrendingUp, Cpu, HardDrive, Network } from 'lucide-react';
import { formatNumber, formatBytes } from '@/lib/utils';
import type { AgentMetrics, SystemMetrics } from '@/types';

/**
 * Resource metric card
 */
function ResourceCard({ 
  icon: Icon, 
  value, 
  label, 
  color,
  showProgress = true,
  extra
}: { 
  icon: React.ElementType; 
  value: number | string; 
  label: string; 
  color: string;
  showProgress?: boolean;
  extra?: React.ReactNode;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between mb-2">
          <Icon className={`w-8 h-8 ${color}`} />
          <span className="text-3xl font-bold">{typeof value === 'number' ? `${value}%` : value}</span>
        </div>
        <p className="text-sm text-muted-foreground">{label}</p>
        {showProgress && typeof value === 'number' && (
          <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className={`h-full ${color.replace('text-', 'bg-')} transition-all`}
              style={{ width: `${value}%` }}
            />
          </div>
        )}
        {extra}
      </CardContent>
    </Card>
  );
}

/**
 * System resources section
 */
function SystemResources({ metrics }: { metrics: SystemMetrics }) {
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">System Resources</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ResourceCard icon={Cpu} value={metrics.cpu_usage} label="CPU Usage" color="text-blue-500" />
        <ResourceCard icon={HardDrive} value={metrics.memory_usage} label="Memory Usage" color="text-purple-500" />
        <ResourceCard icon={HardDrive} value={metrics.disk_usage} label="Disk Usage" color="text-orange-500" />
        <ResourceCard 
          icon={Network} 
          value={metrics.active_connections.toString()} 
          label="Active Connections" 
          color="text-green-500"
          showProgress={false}
          extra={
            <div className="mt-2 text-xs text-muted-foreground">
              ↓ {formatBytes(metrics.network_in)} | ↑ {formatBytes(metrics.network_out)}
            </div>
          }
        />
      </div>
    </div>
  );
}

/**
 * Agent metrics card
 */
function AgentCard({ agent }: { agent: AgentMetrics }) {
  const successRate = agent.requests_total > 0 
    ? (agent.requests_success / agent.requests_total) * 100 
    : 0;

  return (
    <Card className="hover:shadow-lg transition-shadow">
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
              <p className="text-2xl font-bold text-foreground">{formatNumber(agent.requests_total)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Success</p>
              <p className="text-2xl font-bold text-green-500">{formatNumber(agent.requests_success)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Failed</p>
              <p className="text-2xl font-bold text-red-500">{formatNumber(agent.requests_failed)}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Avg Response Time</p>
              <p className="text-lg font-semibold text-foreground">{agent.avg_response_time}ms</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Uptime</p>
              <p className="text-lg font-semibold text-foreground">{agent.uptime.toFixed(2)}%</p>
            </div>
          </div>
          <div className="text-xs text-muted-foreground">Last activity: {agent.last_activity}</div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Empty agents component
 */
function EmptyAgents() {
  return (
    <Card>
      <CardContent className="py-12">
        <div className="text-center">
          <BarChart3 className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">No Agent Metrics</h3>
          <p className="text-muted-foreground">No agent performance data available</p>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Agent performance section
 */
function AgentPerformance({ agents }: { agents: AgentMetrics[] }) {
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Agent Performance</h2>
      {agents.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {agents.map((agent: AgentMetrics) => (
            <AgentCard key={agent.agent_name} agent={agent} />
          ))}
        </div>
      ) : (
        <EmptyAgents />
      )}
    </div>
  );
}

/**
 * Combined data type for the page
 */
interface MetricsData {
  agents: AgentMetrics[];
  system: SystemMetrics;
}

const defaultSystemMetrics: SystemMetrics = {
  cpu_usage: 0,
  memory_usage: 0,
  disk_usage: 0,
  network_in: 0,
  network_out: 0,
  active_connections: 0,
};

/**
 * Metrics page - refactored to use DataPage
 */
export default function MetricsPage() {
  const { data: agents, error: agentsError, isLoading: agentsLoading, mutate: mutateAgents } = useMetrics();
  const { data: system, error: systemError, isLoading: systemLoading } = useSystemMetrics();

  const isLoading = agentsLoading || systemLoading;
  const error = agentsError || systemError;
  
  // Combine data for DataPage
  const combinedData: MetricsData | null = !isLoading && !error ? {
    agents: agents || [],
    system: system || defaultSystemMetrics,
  } : null;

  return (
    <DataPage<MetricsData>
      title="Metrics & Observability"
      description="Monitor system performance and agent metrics"
      isLoading={isLoading}
      error={error}
      data={combinedData}
      onRetry={mutateAgents}
      errorMessage="Could not fetch metrics data from the backend API."
      loadingLayout="grid"
      loadingCount={4}
    >
      {(data) => (
        <div className="space-y-8">
          <SystemResources metrics={data.system} />
          <AgentPerformance agents={data.agents} />
        </div>
      )}
    </DataPage>
  );
}
