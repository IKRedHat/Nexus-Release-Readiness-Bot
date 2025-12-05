'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { useFeatureRequests, mutateAPI } from '@/hooks/useAPI';
import { DataPage } from '@/components/page';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ConfirmDialog, useConfirmDialog } from '@/components/ui/confirm-dialog';
import { FeatureRequestFormDialog, FeatureRequestFormData } from '@/components/features/FeatureRequestFormDialog';
import { Lightbulb, Plus, ThumbsUp, ExternalLink, Loader2 } from 'lucide-react';
import { formatRelativeTime, getStatusColor } from '@/lib/utils';
import { endpoints } from '@/lib/api';
import type { FeatureRequest } from '@/types';

const STATUSES = ['all', 'pending', 'approved', 'in_progress', 'implemented', 'rejected'];

/**
 * Empty state component
 */
function EmptyRequests({ onCreate }: { onCreate: () => void }) {
  return (
    <Card>
      <CardContent className="py-12">
        <div className="text-center">
          <Lightbulb className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">No Feature Requests</h3>
          <p className="text-muted-foreground mb-6">Be the first to submit a feature request!</p>
          <Button onClick={onCreate}>
            <Plus size={20} className="mr-2" />
            Create Request
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Status filters component
 */
function StatusFilters({ filter, onFilterChange }: { filter: string | undefined; onFilterChange: (status: string | undefined) => void }) {
  return (
    <div className="flex gap-2 flex-wrap mb-6">
      {STATUSES.map(status => (
        <Button
          key={status}
          variant={filter === (status === 'all' ? undefined : status) ? 'default' : 'outline'}
          size="sm"
          onClick={() => onFilterChange(status === 'all' ? undefined : status)}
        >
          {status.replace('_', ' ')}
        </Button>
      ))}
    </div>
  );
}

/**
 * Single feature request card
 */
function RequestCard({ 
  request, 
  onVote,
  onView,
  isVoting,
}: { 
  request: FeatureRequest; 
  onVote: (request: FeatureRequest) => void;
  onView: (request: FeatureRequest) => void;
  isVoting: boolean;
}) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg mb-2">{request.title}</CardTitle>
            <div className="flex flex-wrap gap-2">
              <Badge className={getStatusColor(request.status)}>{request.status.replace('_', ' ')}</Badge>
              <Badge className={getStatusColor(request.priority)}>{request.priority}</Badge>
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
          <p className="text-sm text-muted-foreground line-clamp-3">{request.description}</p>

          {request.labels && request.labels.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {request.labels.map((label, i) => (
                <Badge key={i} variant="outline" className="text-xs">{label}</Badge>
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
                href={`https://jira.example.com/browse/${request.jira_ticket}`} 
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline font-medium"
              >
                {request.jira_ticket}
              </a>
              {request.jira_status && (
                <Badge variant="outline" className="ml-auto text-xs">{request.jira_status}</Badge>
              )}
            </div>
          )}

          <div className="flex gap-2">
            <Button 
              size="sm" 
              variant="outline" 
              className="flex-1"
              onClick={() => onVote(request)}
              disabled={isVoting}
            >
              {isVoting ? (
                <Loader2 size={14} className="mr-1 animate-spin" />
              ) : (
                <ThumbsUp size={14} className="mr-1" />
              )}
              Vote
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className="flex-1"
              onClick={() => onView(request)}
            >
              View Details
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Feature Request Detail Dialog
 */
function FeatureRequestDetailDialog({
  open,
  onOpenChange,
  request,
  onVote,
  isVoting,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  request: FeatureRequest | null;
  onVote: () => void;
  isVoting: boolean;
}) {
  if (!request) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between gap-4">
            <div>
              <DialogTitle className="text-xl">{request.title}</DialogTitle>
              <div className="flex gap-2 mt-2">
                <Badge className={getStatusColor(request.status)}>{request.status.replace('_', ' ')}</Badge>
                <Badge className={getStatusColor(request.priority)}>{request.priority} priority</Badge>
              </div>
            </div>
            <Button onClick={onVote} disabled={isVoting} variant="outline">
              {isVoting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <ThumbsUp className="w-4 h-4 mr-2" />
              )}
              {request.votes} votes
            </Button>
          </div>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div>
            <h4 className="font-semibold mb-2">Description</h4>
            <p className="text-muted-foreground whitespace-pre-wrap">{request.description}</p>
          </div>

          {request.labels && request.labels.length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">Labels</h4>
              <div className="flex flex-wrap gap-2">
                {request.labels.map((label, i) => (
                  <Badge key={i} variant="outline">{label}</Badge>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Requested by:</span>
              <p className="font-medium">{request.requested_by}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Created:</span>
              <p className="font-medium">{formatRelativeTime(request.created_at)}</p>
            </div>
            {request.assigned_to && (
              <div>
                <span className="text-muted-foreground">Assigned to:</span>
                <p className="font-medium">{request.assigned_to}</p>
              </div>
            )}
            {request.jira_ticket && (
              <div>
                <span className="text-muted-foreground">Jira Ticket:</span>
                <a 
                  href={`https://jira.example.com/browse/${request.jira_ticket}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-blue-500 hover:underline flex items-center gap-1"
                >
                  {request.jira_ticket}
                  <ExternalLink size={12} />
                </a>
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Import Dialog components
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

/**
 * Feature requests page with full CRUD and voting functionality
 */
export default function FeatureRequestsPage() {
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const { data: requests, error, isLoading, mutate } = useFeatureRequests(filter);
  
  // Form dialog state
  const [formOpen, setFormOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<FeatureRequest | null>(null);
  
  // Detail dialog state
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailRequest, setDetailRequest] = useState<FeatureRequest | null>(null);
  
  // Voting state
  const [votingId, setVotingId] = useState<string | null>(null);

  // Open create dialog
  const handleCreate = () => {
    setSelectedRequest(null);
    setFormOpen(true);
  };

  // View detail
  const handleView = (request: FeatureRequest) => {
    setDetailRequest(request);
    setDetailOpen(true);
  };

  // Handle vote
  const handleVote = async (request: FeatureRequest) => {
    setVotingId(request.id);
    try {
      await mutateAPI(`${endpoints.featureRequests}/${request.id}/vote`, 'POST');
      toast.success('Vote Recorded', {
        description: `You voted for "${request.title}"`,
      });
      mutate();
    } catch (error: any) {
      toast.error('Vote Failed', {
        description: error.response?.data?.detail || 'Failed to record vote. You may have already voted.',
      });
    } finally {
      setVotingId(null);
    }
  };

  // Handle form submission
  const handleFormSubmit = async (data: FeatureRequestFormData) => {
    try {
      if (selectedRequest) {
        await mutateAPI(
          `${endpoints.featureRequests}/${selectedRequest.id}`,
          'PUT',
          data
        );
        toast.success('Request Updated', {
          description: `Feature request has been updated successfully.`,
        });
      } else {
        await mutateAPI(endpoints.featureRequests, 'POST', data);
        toast.success('Request Submitted', {
          description: `Your feature request has been submitted successfully.`,
        });
      }
      mutate();
    } catch (error: any) {
      toast.error('Operation Failed', {
        description: error.response?.data?.detail || 'Failed to save feature request.',
      });
      throw error;
    }
  };

  return (
    <>
      <DataPage
        title="Feature Requests"
        description="Submit and track feature requests for the platform"
        isLoading={isLoading}
        error={error}
        data={requests}
        onRetry={mutate}
        errorMessage="Could not fetch feature requests from the backend API."
        loadingLayout="grid"
        loadingCount={4}
        emptyState={<EmptyRequests onCreate={handleCreate} />}
        actions={
          <Button className="gap-2" onClick={handleCreate}>
            <Plus size={20} />
            New Request
          </Button>
        }
      >
        {(requestsList) => (
          <div className="space-y-6">
            <StatusFilters filter={filter} onFilterChange={setFilter} />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {requestsList.map((request: FeatureRequest) => (
                <RequestCard 
                  key={request.id} 
                  request={request}
                  onVote={handleVote}
                  onView={handleView}
                  isVoting={votingId === request.id}
                />
              ))}
            </div>
          </div>
        )}
      </DataPage>

      {/* Create/Edit Dialog */}
      <FeatureRequestFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        featureRequest={selectedRequest}
        onSubmit={handleFormSubmit}
      />

      {/* Detail Dialog */}
      <FeatureRequestDetailDialog
        open={detailOpen}
        onOpenChange={setDetailOpen}
        request={detailRequest}
        onVote={() => detailRequest && handleVote(detailRequest)}
        isVoting={!!detailRequest && votingId === detailRequest.id}
      />
    </>
  );
}
