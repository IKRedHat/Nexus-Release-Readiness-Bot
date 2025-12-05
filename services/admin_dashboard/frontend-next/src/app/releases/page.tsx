'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { useReleases, mutateAPI } from '@/hooks/useAPI';
import { DataPage } from '@/components/page';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ConfirmDialog, useConfirmDialog } from '@/components/ui/confirm-dialog';
import { ReleaseFormDialog, ReleaseFormData } from '@/components/releases/ReleaseFormDialog';
import { Calendar, Plus, Edit, Trash2 } from 'lucide-react';
import { formatDate, getStatusColor } from '@/lib/utils';
import { endpoints } from '@/lib/api';
import type { Release } from '@/types';

/**
 * Empty state component for releases
 */
function EmptyReleases({ onCreate }: { onCreate: () => void }) {
  return (
    <Card>
      <CardContent className="py-12">
        <div className="text-center">
          <Calendar className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">No Releases Yet</h3>
          <p className="text-muted-foreground mb-6">
            Create your first release to get started
          </p>
          <Button onClick={onCreate}>
            <Plus size={20} className="mr-2" />
            Create Release
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Release stats cards
 */
function ReleaseStats({ releases }: { releases: Release[] }) {
  const stats = [
    { label: 'Total Releases', value: releases.length, color: 'text-foreground' },
    { label: 'In Progress', value: releases.filter(r => r.status === 'in_progress').length, color: 'text-blue-500' },
    { label: 'Completed', value: releases.filter(r => r.status === 'completed').length, color: 'text-green-500' },
    { label: 'Planned', value: releases.filter(r => r.status === 'planned').length, color: 'text-purple-500' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      {stats.map(stat => (
        <Card key={stat.label}>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/**
 * Single release card
 */
function ReleaseCard({ 
  release, 
  onEdit, 
  onDelete 
}: { 
  release: Release; 
  onEdit: (release: Release) => void;
  onDelete: (release: Release) => void;
}) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-xl mb-1">{release.version}</CardTitle>
            <p className="text-sm text-muted-foreground">{release.name}</p>
          </div>
          <Badge className={getStatusColor(release.status)}>
            {release.status.replace('_', ' ')}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {release.description || 'No description available'}
          </p>

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar size={16} />
            <span>{formatDate(release.target_date)}</span>
          </div>

          {release.features && release.features.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-foreground mb-1">
                Features ({release.features.length})
              </p>
              <div className="flex flex-wrap gap-1">
                {release.features.slice(0, 3).map((feature, i) => (
                  <Badge key={i} variant="outline" className="text-xs">{feature}</Badge>
                ))}
                {release.features.length > 3 && (
                  <Badge variant="outline" className="text-xs">+{release.features.length - 3}</Badge>
                )}
              </div>
            </div>
          )}

          <div className="flex items-center gap-2 pt-2 border-t border-border">
            <Button 
              size="sm" 
              variant="outline" 
              className="flex-1"
              onClick={() => onEdit(release)}
            >
              <Edit size={16} className="mr-1" />
              Edit
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className="flex-1 text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={() => onDelete(release)}
            >
              <Trash2 size={16} className="mr-1" />
              Delete
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Releases page with full CRUD functionality
 */
export default function ReleasesPage() {
  const { data: releases, error, isLoading, mutate } = useReleases();
  
  // Form dialog state
  const [formOpen, setFormOpen] = useState(false);
  const [selectedRelease, setSelectedRelease] = useState<Release | null>(null);
  
  // Delete confirmation dialog state
  const deleteConfirm = useConfirmDialog<Release>();

  // Open create dialog
  const handleCreate = () => {
    setSelectedRelease(null);
    setFormOpen(true);
  };

  // Open edit dialog
  const handleEdit = (release: Release) => {
    setSelectedRelease(release);
    setFormOpen(true);
  };

  // Handle form submission (create or update)
  const handleFormSubmit = async (data: ReleaseFormData) => {
    try {
      if (selectedRelease) {
        // Update existing release
        await mutateAPI(
          `${endpoints.releases}/${selectedRelease.id}`,
          'PUT',
          { ...data, target_date: `${data.target_date}T10:00:00Z` }
        );
        toast.success('Release Updated', {
          description: `Release ${data.version} has been updated successfully.`,
        });
      } else {
        // Create new release
        await mutateAPI(
          endpoints.releases,
          'POST',
          { ...data, target_date: `${data.target_date}T10:00:00Z` }
        );
        toast.success('Release Created', {
          description: `Release ${data.version} has been created successfully.`,
        });
      }
      // Refresh the releases list
      mutate();
    } catch (error: any) {
      toast.error('Operation Failed', {
        description: error.response?.data?.detail || 'Failed to save release. Please try again.',
      });
      throw error; // Re-throw to let the dialog handle it
    }
  };

  // Handle delete confirmation
  const handleDelete = async () => {
    if (!deleteConfirm.item) return;
    
    try {
      await mutateAPI(`${endpoints.releases}/${deleteConfirm.item.id}`, 'DELETE');
      toast.success('Release Deleted', {
        description: `Release ${deleteConfirm.item.version} has been deleted.`,
      });
      mutate();
    } catch (error: any) {
      toast.error('Delete Failed', {
        description: error.response?.data?.detail || 'Failed to delete release. Please try again.',
      });
      throw error;
    }
  };

  return (
    <>
      <DataPage
        title="Releases"
        description="Manage and track all software releases"
        isLoading={isLoading}
        error={error}
        data={releases}
        onRetry={mutate}
        errorMessage="Could not fetch releases from the backend API."
        loadingLayout="grid"
        loadingCount={6}
        emptyState={<EmptyReleases onCreate={handleCreate} />}
        actions={
          <Button className="gap-2" onClick={handleCreate}>
            <Plus size={20} />
            New Release
          </Button>
        }
      >
        {(releasesList) => (
          <div className="space-y-6">
            <ReleaseStats releases={releasesList} />
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {releasesList.map((release: Release) => (
                <ReleaseCard 
                  key={release.id} 
                  release={release}
                  onEdit={handleEdit}
                  onDelete={deleteConfirm.openConfirm}
                />
              ))}
            </div>
          </div>
        )}
      </DataPage>

      {/* Create/Edit Dialog */}
      <ReleaseFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        release={selectedRelease}
        onSubmit={handleFormSubmit}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteConfirm.isOpen}
        onOpenChange={deleteConfirm.setIsOpen}
        title="Delete Release"
        description={`Are you sure you want to delete release "${deleteConfirm.item?.version}"? This action cannot be undone.`}
        variant="danger"
        confirmText="Delete Release"
        onConfirm={handleDelete}
      />
    </>
  );
}
