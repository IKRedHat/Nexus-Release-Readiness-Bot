'use client';

import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import type { Release } from '@/types';
import { RELEASE_STATUSES } from '@/lib/constants';

export interface ReleaseFormDialogProps {
  /** Whether dialog is open */
  open: boolean;
  /** Callback when dialog should close */
  onOpenChange: (open: boolean) => void;
  /** Release to edit (null for create) */
  release?: Release | null;
  /** Callback when form is submitted */
  onSubmit: (data: ReleaseFormData) => Promise<void>;
}

export interface ReleaseFormData {
  version: string;
  name: string;
  description: string;
  release_date: string;
  status: Release['status'];
  features: string[];
}

const initialFormData: ReleaseFormData = {
  version: '',
  name: '',
  description: '',
  release_date: new Date().toISOString().split('T')[0],
  status: 'planned',
  features: [],
};

/**
 * ReleaseFormDialog Component
 * 
 * Dialog for creating and editing releases.
 * 
 * @example
 * <ReleaseFormDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   release={selectedRelease}
 *   onSubmit={handleSaveRelease}
 * />
 */
export function ReleaseFormDialog({
  open,
  onOpenChange,
  release,
  onSubmit,
}: ReleaseFormDialogProps) {
  const [formData, setFormData] = useState<ReleaseFormData>(initialFormData);
  const [featureInput, setFeatureInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof ReleaseFormData, string>>>({});

  const isEditing = !!release;

  // Reset form when dialog opens/closes or release changes
  useEffect(() => {
    if (open) {
      if (release) {
        setFormData({
          version: release.version,
          name: release.name,
          description: release.description || '',
          release_date: release.release_date.split('T')[0],
          status: release.status,
          features: release.features || [],
        });
      } else {
        setFormData(initialFormData);
      }
      setFeatureInput('');
      setErrors({});
    }
  }, [open, release]);

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof ReleaseFormData, string>> = {};

    if (!formData.version.trim()) {
      newErrors.version = 'Version is required';
    } else if (!/^\d+\.\d+\.\d+$/.test(formData.version.trim())) {
      newErrors.version = 'Version must be in format X.Y.Z (e.g., 2.1.0)';
    }

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.release_date) {
      newErrors.release_date = 'Release date is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to save release:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddFeature = () => {
    if (featureInput.trim()) {
      setFormData(prev => ({
        ...prev,
        features: [...prev.features, featureInput.trim()],
      }));
      setFeatureInput('');
    }
  };

  const handleRemoveFeature = (index: number) => {
    setFormData(prev => ({
      ...prev,
      features: prev.features.filter((_, i) => i !== index),
    }));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddFeature();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit Release' : 'Create New Release'}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the release details below.'
              : 'Fill in the details to create a new release.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Version */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Version <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.version}
              onChange={(e) => setFormData(prev => ({ ...prev, version: e.target.value }))}
              placeholder="e.g., 2.1.0"
              disabled={isSubmitting}
            />
            {errors.version && (
              <p className="text-sm text-red-500">{errors.version}</p>
            )}
          </div>

          {/* Name */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Release Name <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Feature Release"
              disabled={isSubmitting}
            />
            {errors.name && (
              <p className="text-sm text-red-500">{errors.name}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Describe the release..."
              rows={3}
              disabled={isSubmitting}
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Release Date */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Release Date <span className="text-red-500">*</span>
            </label>
            <Input
              type="date"
              value={formData.release_date}
              onChange={(e) => setFormData(prev => ({ ...prev, release_date: e.target.value }))}
              disabled={isSubmitting}
            />
            {errors.release_date && (
              <p className="text-sm text-red-500">{errors.release_date}</p>
            )}
          </div>

          {/* Status */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Status</label>
            <div className="flex flex-wrap gap-2">
              {RELEASE_STATUSES.map((status) => (
                <Button
                  key={status.value}
                  type="button"
                  variant={formData.status === status.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setFormData(prev => ({ ...prev, status: status.value as Release['status'] }))}
                  disabled={isSubmitting}
                >
                  {status.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Features */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Features</label>
            <div className="flex gap-2">
              <Input
                value={featureInput}
                onChange={(e) => setFeatureInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Add a feature..."
                disabled={isSubmitting}
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleAddFeature}
                disabled={isSubmitting || !featureInput.trim()}
              >
                Add
              </Button>
            </div>
            {formData.features.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.features.map((feature, index) => (
                  <Badge
                    key={index}
                    variant="outline"
                    className="cursor-pointer hover:bg-destructive/10"
                    onClick={() => handleRemoveFeature(index)}
                  >
                    {feature} ×
                  </Badge>
                ))}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              Press Enter or click Add to add features. Click a feature to remove it.
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {isEditing ? 'Saving...' : 'Creating...'}
                </>
              ) : (
                isEditing ? 'Save Changes' : 'Create Release'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

