/**
 * Audit Log Page
 * 
 * Comprehensive audit trail for all system activities.
 * Features:
 * - Full activity history
 * - Advanced filtering (user, action, resource, date range)
 * - Real-time updates
 * - Export functionality
 * - Search
 */

'use client';

import { useState, useMemo, useCallback } from 'react';
import { format, subDays, startOfDay, endOfDay, parseISO } from 'date-fns';
import {
  Search,
  Filter,
  Download,
  RefreshCw,
  User,
  Calendar,
  Clock,
  Shield,
  Settings,
  FileText,
  Package,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  ChevronDown,
  X,
} from 'lucide-react';
import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ExportButton } from '@/components/ui/export-button';
import { cn } from '@/lib/utils';
import type { ExportColumn } from '@/lib/export';

// =============================================================================
// Types
// =============================================================================

interface AuditLogEntry {
  id: string;
  timestamp: string;
  user: {
    id: string;
    name: string;
    email: string;
  };
  action: 'create' | 'update' | 'delete' | 'login' | 'logout' | 'view' | 'export' | 'config_change';
  resource: 'release' | 'feature_request' | 'user' | 'role' | 'config' | 'session' | 'system';
  resourceId?: string;
  resourceName?: string;
  details?: string;
  metadata?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
  status: 'success' | 'failure' | 'warning';
}

interface FilterState {
  search: string;
  users: string[];
  actions: string[];
  resources: string[];
  status: string[];
  dateFrom: Date | null;
  dateTo: Date | null;
}

// =============================================================================
// Mock Data (Replace with API call)
// =============================================================================

const MOCK_AUDIT_LOG: AuditLogEntry[] = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    user: { id: 'u1', name: 'John Doe', email: 'john@nexus.dev' },
    action: 'create',
    resource: 'release',
    resourceId: 'r1',
    resourceName: 'v2.5.0',
    details: 'Created new release version 2.5.0',
    status: 'success',
  },
  {
    id: '2',
    timestamp: subDays(new Date(), 0.1).toISOString(),
    user: { id: 'u2', name: 'Jane Smith', email: 'jane@nexus.dev' },
    action: 'update',
    resource: 'config',
    details: 'Updated Jira integration settings',
    status: 'success',
  },
  {
    id: '3',
    timestamp: subDays(new Date(), 0.2).toISOString(),
    user: { id: 'u1', name: 'John Doe', email: 'john@nexus.dev' },
    action: 'login',
    resource: 'session',
    details: 'User logged in successfully',
    ipAddress: '192.168.1.100',
    status: 'success',
  },
  {
    id: '4',
    timestamp: subDays(new Date(), 0.3).toISOString(),
    user: { id: 'u3', name: 'Admin User', email: 'admin@nexus.dev' },
    action: 'delete',
    resource: 'user',
    resourceId: 'u5',
    resourceName: 'test@test.com',
    details: 'Deleted user account',
    status: 'success',
  },
  {
    id: '5',
    timestamp: subDays(new Date(), 0.5).toISOString(),
    user: { id: 'u2', name: 'Jane Smith', email: 'jane@nexus.dev' },
    action: 'create',
    resource: 'feature_request',
    resourceId: 'fr1',
    resourceName: 'Dark mode support',
    details: 'Submitted new feature request',
    status: 'success',
  },
  {
    id: '6',
    timestamp: subDays(new Date(), 1).toISOString(),
    user: { id: 'u1', name: 'John Doe', email: 'john@nexus.dev' },
    action: 'config_change',
    resource: 'system',
    details: 'Switched system to production mode',
    status: 'warning',
  },
  {
    id: '7',
    timestamp: subDays(new Date(), 1.5).toISOString(),
    user: { id: 'u4', name: 'Unknown User', email: 'unknown@test.com' },
    action: 'login',
    resource: 'session',
    details: 'Failed login attempt - invalid credentials',
    ipAddress: '10.0.0.1',
    status: 'failure',
  },
  {
    id: '8',
    timestamp: subDays(new Date(), 2).toISOString(),
    user: { id: 'u3', name: 'Admin User', email: 'admin@nexus.dev' },
    action: 'update',
    resource: 'role',
    resourceId: 'role1',
    resourceName: 'Developer',
    details: 'Updated role permissions',
    status: 'success',
  },
];

// =============================================================================
// Constants
// =============================================================================

const ACTION_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  create: { icon: CheckCircle, color: 'text-green-500', label: 'Create' },
  update: { icon: RefreshCw, color: 'text-blue-500', label: 'Update' },
  delete: { icon: XCircle, color: 'text-red-500', label: 'Delete' },
  login: { icon: User, color: 'text-purple-500', label: 'Login' },
  logout: { icon: User, color: 'text-gray-500', label: 'Logout' },
  view: { icon: Info, color: 'text-cyan-500', label: 'View' },
  export: { icon: Download, color: 'text-orange-500', label: 'Export' },
  config_change: { icon: Settings, color: 'text-yellow-500', label: 'Config Change' },
};

const RESOURCE_CONFIG: Record<string, { icon: React.ElementType; label: string }> = {
  release: { icon: Package, label: 'Release' },
  feature_request: { icon: FileText, label: 'Feature Request' },
  user: { icon: User, label: 'User' },
  role: { icon: Shield, label: 'Role' },
  config: { icon: Settings, label: 'Configuration' },
  session: { icon: Clock, label: 'Session' },
  system: { icon: AlertCircle, label: 'System' },
};

const STATUS_COLORS: Record<string, string> = {
  success: 'bg-green-500/10 text-green-500 border-green-500/20',
  failure: 'bg-red-500/10 text-red-500 border-red-500/20',
  warning: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
};

// =============================================================================
// Component
// =============================================================================

export default function AuditLogPage() {
  const [entries] = useState<AuditLogEntry[]>(MOCK_AUDIT_LOG);
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    users: [],
    actions: [],
    resources: [],
    status: [],
    dateFrom: subDays(new Date(), 7),
    dateTo: new Date(),
  });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<AuditLogEntry | null>(null);

  // Get unique values for filter options
  const filterOptions = useMemo(() => ({
    users: [...new Set(entries.map(e => e.user.name))],
    actions: [...new Set(entries.map(e => e.action))],
    resources: [...new Set(entries.map(e => e.resource))],
  }), [entries]);

  // Filter entries
  const filteredEntries = useMemo(() => {
    return entries.filter(entry => {
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        const matchesSearch = 
          entry.user.name.toLowerCase().includes(searchLower) ||
          entry.user.email.toLowerCase().includes(searchLower) ||
          entry.details?.toLowerCase().includes(searchLower) ||
          entry.resourceName?.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }

      // User filter
      if (filters.users.length > 0 && !filters.users.includes(entry.user.name)) {
        return false;
      }

      // Action filter
      if (filters.actions.length > 0 && !filters.actions.includes(entry.action)) {
        return false;
      }

      // Resource filter
      if (filters.resources.length > 0 && !filters.resources.includes(entry.resource)) {
        return false;
      }

      // Status filter
      if (filters.status.length > 0 && !filters.status.includes(entry.status)) {
        return false;
      }

      // Date range filter
      const entryDate = parseISO(entry.timestamp);
      if (filters.dateFrom && entryDate < startOfDay(filters.dateFrom)) {
        return false;
      }
      if (filters.dateTo && entryDate > endOfDay(filters.dateTo)) {
        return false;
      }

      return true;
    });
  }, [entries, filters]);

  // Toggle filter array
  const toggleFilter = useCallback((key: keyof FilterState, value: string) => {
    setFilters(prev => {
      const arr = prev[key] as string[];
      const newArr = arr.includes(value)
        ? arr.filter(v => v !== value)
        : [...arr, value];
      return { ...prev, [key]: newArr };
    });
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setFilters({
      search: '',
      users: [],
      actions: [],
      resources: [],
      status: [],
      dateFrom: subDays(new Date(), 7),
      dateTo: new Date(),
    });
  }, []);

  // Export columns
  const exportColumns: ExportColumn<AuditLogEntry>[] = [
    { key: 'timestamp', header: 'Timestamp', formatter: (v) => format(parseISO(v as string), 'yyyy-MM-dd HH:mm:ss') },
    { key: 'user.name', header: 'User' },
    { key: 'user.email', header: 'Email' },
    { key: 'action', header: 'Action' },
    { key: 'resource', header: 'Resource' },
    { key: 'resourceName', header: 'Resource Name' },
    { key: 'details', header: 'Details' },
    { key: 'status', header: 'Status' },
    { key: 'ipAddress', header: 'IP Address' },
  ];

  const activeFiltersCount = 
    filters.users.length + 
    filters.actions.length + 
    filters.resources.length + 
    filters.status.length;

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Audit Log</h1>
            <p className="text-muted-foreground mt-1">
              Complete activity history and system events
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ExportButton
              data={filteredEntries as unknown as Record<string, unknown>[]}
              columns={exportColumns as ExportColumn<Record<string, unknown>>[]}
              filename="audit-log"
              title="Nexus Audit Log"
            />
            <Button variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-foreground">{filteredEntries.length}</p>
                <p className="text-sm text-muted-foreground">Total Events</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-green-500">
                  {filteredEntries.filter(e => e.status === 'success').length}
                </p>
                <p className="text-sm text-muted-foreground">Successful</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-red-500">
                  {filteredEntries.filter(e => e.status === 'failure').length}
                </p>
                <p className="text-sm text-muted-foreground">Failed</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-yellow-500">
                  {filteredEntries.filter(e => e.status === 'warning').length}
                </p>
                <p className="text-sm text-muted-foreground">Warnings</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col gap-4">
              {/* Search Row */}
              <div className="flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by user, details, or resource..."
                    value={filters.search}
                    onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                    className="pl-10"
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={() => setShowFilters(!showFilters)}
                  className={cn(activeFiltersCount > 0 && 'border-primary')}
                >
                  <Filter className="w-4 h-4 mr-2" />
                  Filters
                  {activeFiltersCount > 0 && (
                    <Badge className="ml-2" variant="secondary">{activeFiltersCount}</Badge>
                  )}
                  <ChevronDown className={cn('w-4 h-4 ml-2 transition-transform', showFilters && 'rotate-180')} />
                </Button>
                {activeFiltersCount > 0 && (
                  <Button variant="ghost" size="sm" onClick={clearFilters}>
                    <X className="w-4 h-4 mr-1" />
                    Clear
                  </Button>
                )}
              </div>

              {/* Filter Panel */}
              {showFilters && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-border">
                  {/* Actions */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Actions</label>
                    <div className="flex flex-wrap gap-1">
                      {filterOptions.actions.map(action => (
                        <Badge
                          key={action}
                          variant={filters.actions.includes(action) ? 'default' : 'outline'}
                          className="cursor-pointer"
                          onClick={() => toggleFilter('actions', action)}
                        >
                          {ACTION_CONFIG[action]?.label || action}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Resources */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Resources</label>
                    <div className="flex flex-wrap gap-1">
                      {filterOptions.resources.map(resource => (
                        <Badge
                          key={resource}
                          variant={filters.resources.includes(resource) ? 'default' : 'outline'}
                          className="cursor-pointer"
                          onClick={() => toggleFilter('resources', resource)}
                        >
                          {RESOURCE_CONFIG[resource]?.label || resource}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Status */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Status</label>
                    <div className="flex flex-wrap gap-1">
                      {['success', 'failure', 'warning'].map(status => (
                        <Badge
                          key={status}
                          variant={filters.status.includes(status) ? 'default' : 'outline'}
                          className="cursor-pointer capitalize"
                          onClick={() => toggleFilter('status', status)}
                        >
                          {status}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Date Range */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Date Range</label>
                    <div className="flex gap-2">
                      <Input
                        type="date"
                        value={filters.dateFrom ? format(filters.dateFrom, 'yyyy-MM-dd') : ''}
                        onChange={(e) => setFilters(prev => ({
                          ...prev,
                          dateFrom: e.target.value ? new Date(e.target.value) : null
                        }))}
                        className="text-sm"
                      />
                      <Input
                        type="date"
                        value={filters.dateTo ? format(filters.dateTo, 'yyyy-MM-dd') : ''}
                        onChange={(e) => setFilters(prev => ({
                          ...prev,
                          dateTo: e.target.value ? new Date(e.target.value) : null
                        }))}
                        className="text-sm"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Audit Log Entries */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Activity Log</span>
              <span className="text-sm font-normal text-muted-foreground">
                Showing {filteredEntries.length} entries
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {filteredEntries.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No audit log entries found matching your filters</p>
                </div>
              ) : (
                filteredEntries.map(entry => {
                  const ActionIcon = ACTION_CONFIG[entry.action]?.icon || Info;
                  const ResourceIcon = RESOURCE_CONFIG[entry.resource]?.icon || FileText;
                  
                  return (
                    <div
                      key={entry.id}
                      className={cn(
                        'flex items-start gap-4 p-4 rounded-lg border transition-colors cursor-pointer',
                        'hover:bg-muted/50',
                        selectedEntry?.id === entry.id && 'bg-muted'
                      )}
                      onClick={() => setSelectedEntry(selectedEntry?.id === entry.id ? null : entry)}
                    >
                      {/* Status Icon */}
                      <div className={cn(
                        'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0',
                        STATUS_COLORS[entry.status]
                      )}>
                        <ActionIcon className="w-5 h-5" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium">{entry.user.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {ACTION_CONFIG[entry.action]?.label || entry.action}
                          </Badge>
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <ResourceIcon className="w-3 h-3" />
                            <span className="text-xs">{RESOURCE_CONFIG[entry.resource]?.label}</span>
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground">{entry.details}</p>
                        {entry.resourceName && (
                          <p className="text-sm mt-1">
                            <span className="text-muted-foreground">Resource:</span>{' '}
                            <span className="font-medium">{entry.resourceName}</span>
                          </p>
                        )}
                        
                        {/* Expanded Details */}
                        {selectedEntry?.id === entry.id && (
                          <div className="mt-3 pt-3 border-t border-border space-y-2 text-sm">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <span className="text-muted-foreground">Email:</span>{' '}
                                <span>{entry.user.email}</span>
                              </div>
                              {entry.ipAddress && (
                                <div>
                                  <span className="text-muted-foreground">IP Address:</span>{' '}
                                  <span>{entry.ipAddress}</span>
                                </div>
                              )}
                              {entry.resourceId && (
                                <div>
                                  <span className="text-muted-foreground">Resource ID:</span>{' '}
                                  <code className="text-xs bg-muted px-1 py-0.5 rounded">{entry.resourceId}</code>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Timestamp */}
                      <div className="text-right text-sm text-muted-foreground flex-shrink-0">
                        <div>{format(parseISO(entry.timestamp), 'MMM d, yyyy')}</div>
                        <div>{format(parseISO(entry.timestamp), 'HH:mm:ss')}</div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}

