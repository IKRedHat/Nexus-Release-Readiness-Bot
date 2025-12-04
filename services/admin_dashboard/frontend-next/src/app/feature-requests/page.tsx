'use client';

import { useFeatureRequests } from '@/hooks/useAPI';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Layout from '@/components/Layout';
import { Lightbulb, Plus, ThumbsUp, AlertCircle, ExternalLink } from 'lucide-react';
import { formatRelativeTime, getStatusColor } from '@/lib/utils';
import type { FeatureRequest } from '@/types';
import { useState } from 'react';

export default function FeatureRequestsPage() {
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const { data: requests, error, isLoading } = useFeatureRequests(filter);

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-8">
          <Skeleton className="h-10 w-48" />
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-10 w-24" />)}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-64" />)}
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
              <h2 className="text-2xl font-bold mb-2">Unable to Load Feature Requests</h2>
              <p className="text-muted-foreground mb-6">
                Could not fetch feature requests from the backend API.
              </p>
              <Button onClick={() => window.location.reload()}>Retry</Button>
            </div>
          </CardContent>
        </Card>
      </Layout>
    );
  }

  const requestsList = requests || [];
  const statuses = ['all', 'pending', 'approved', 'in_progress', 'implemented', 'rejected'];

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">Feature Requests</h1>
            <p className="text-muted-foreground">
              Submit and track feature requests for the platform
            </p>
          </div>
          <Button className="gap-2">
            <Plus size={20} />
            New Request
          </Button>
        </div>

        {/* Filters */}
        <div className="flex gap-2 flex-wrap">
          {statuses.map(status => (
            <Button
              key={status}
              variant={filter === (status === 'all' ? undefined : status) ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(status === 'all' ? undefined : status)}
            >
              {status.replace('_', ' ')}
            </Button>
          ))}
        </div>

        {/* Feature Requests Grid */}
        {requestsList.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {requestsList.map((request: FeatureRequest) => (
              <Card key={request.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-lg mb-2">{request.title}</CardTitle>
                      <div className="flex flex-wrap gap-2">
                        <Badge className={getStatusColor(request.status)}>
                          {request.status.replace('_', ' ')}
                        </Badge>
                        <Badge className={getStatusColor(request.priority)}>
                          {request.priority}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 px-3 py-1 bg-primary/10 rounded-lg">
                      <ThumbsUp size={16} className="text-primary" />
                      <span className="font-semibold text-primary">{request.votes}</span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {request.description}
                    </p>

                    {request.labels && request.labels.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {request.labels.map((label, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {label}
                          </Badge>
                        ))}
                      </div>
                    )}

                    <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border">
                      <span>Requested by {request.requested_by}</span>
                      <span>{formatRelativeTime(request.created_at)}</span>
                    </div>

                    {request.jira_ticket && (
                      <div className="flex items-center gap-2 p-2 bg-blue-500/10 rounded text-xs">
                        <ExternalLink size={14} className="text-blue-500" />
                        <a 
                          href="#" 
                          className="text-blue-500 hover:underline font-medium"
                        >
                          {request.jira_ticket}
                        </a>
                        {request.jira_status && (
                          <Badge variant="outline" className="ml-auto text-xs">
                            {request.jira_status}
                          </Badge>
                        )}
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" className="flex-1">
                        <ThumbsUp size={14} className="mr-1" />
                        Vote
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1">
                        View Details
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
                <Lightbulb className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Feature Requests</h3>
                <p className="text-muted-foreground mb-6">
                  Be the first to submit a feature request!
                </p>
                <Button>
                  <Plus size={20} className="mr-2" />
                  Create Request
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}

