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
import type { FeatureRequest } from '@/types';
import { FEATURE_STATUSES, PRIORITY_LEVELS } from '@/lib/constants';

export interface FeatureRequestFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  featureRequest?: FeatureRequest | null;
  onSubmit: (data: FeatureRequestFormData) => Promise<void>;
}

export interface FeatureRequestFormData {
  title: string;
  description: string;
  priority: FeatureRequest['priority'];
  status: FeatureRequest['status'];
  labels: string[];
}

const initialFormData: FeatureRequestFormData = {
  title: '',
  description: '',
  priority: 'medium',
  status: 'pending',
  labels: [],
};

/**
 * FeatureRequestFormDialog Component
 * 
 * Dialog for creating and editing feature requests.
 */
export function FeatureRequestFormDialog({
  open,
  onOpenChange,
  featureRequest,
  onSubmit,
}: FeatureRequestFormDialogProps) {
  const [formData, setFormData] = useState<FeatureRequestFormData>(initialFormData);
  const [labelInput, setLabelInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof FeatureRequestFormData, string>>>({});

  const isEditing = !!featureRequest;

  useEffect(() => {
    if (open) {
      if (featureRequest) {
        setFormData({
          title: featureRequest.title,
          description: featureRequest.description,
          priority: featureRequest.priority,
          status: featureRequest.status,
          labels: featureRequest.labels || [],
        });
      } else {
        setFormData(initialFormData);
      }
      setLabelInput('');
      setErrors({});
    }
  }, [open, featureRequest]);

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof FeatureRequestFormData, string>> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.length < 5) {
      newErrors.title = 'Title must be at least 5 characters';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    } else if (formData.description.length < 20) {
      newErrors.description = 'Description must be at least 20 characters';
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
      console.error('Failed to save feature request:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddLabel = () => {
    if (labelInput.trim() && !formData.labels.includes(labelInput.trim().toLowerCase())) {
      setFormData(prev => ({
        ...prev,
        labels: [...prev.labels, labelInput.trim().toLowerCase()],
      }));
      setLabelInput('');
    }
  };

  const handleRemoveLabel = (label: string) => {
    setFormData(prev => ({
      ...prev,
      labels: prev.labels.filter(l => l !== label),
    }));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddLabel();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit Feature Request' : 'Submit Feature Request'}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the feature request details.'
              : 'Describe the feature you would like to see implemented.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Title <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              placeholder="e.g., Add dark mode support"
              disabled={isSubmitting}
            />
            {errors.title && (
              <p className="text-sm text-red-500">{errors.title}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Describe the feature in detail. Why is it needed? What problem does it solve?"
              rows={4}
              disabled={isSubmitting}
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description}</p>
            )}
            <p className="text-xs text-muted-foreground">
              {formData.description.length}/20 minimum characters
            </p>
          </div>

          {/* Priority */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Priority</label>
            <div className="flex flex-wrap gap-2">
              {PRIORITY_LEVELS.map((priority) => (
                <Button
                  key={priority.value}
                  type="button"
                  variant={formData.priority === priority.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setFormData(prev => ({ ...prev, priority: priority.value as FeatureRequest['priority'] }))}
                  disabled={isSubmitting}
                >
                  {priority.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Status (only for editing) */}
          {isEditing && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Status</label>
              <div className="flex flex-wrap gap-2">
                {FEATURE_STATUSES.map((status) => (
                  <Button
                    key={status.value}
                    type="button"
                    variant={formData.status === status.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFormData(prev => ({ ...prev, status: status.value as FeatureRequest['status'] }))}
                    disabled={isSubmitting}
                  >
                    {status.label}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Labels */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Labels</label>
            <div className="flex gap-2">
              <Input
                value={labelInput}
                onChange={(e) => setLabelInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="e.g., ui, api, performance"
                disabled={isSubmitting}
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleAddLabel}
                disabled={isSubmitting || !labelInput.trim()}
              >
                Add
              </Button>
            </div>
            {formData.labels.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.labels.map((label) => (
                  <Badge
                    key={label}
                    variant="outline"
                    className="cursor-pointer hover:bg-destructive/10"
                    onClick={() => handleRemoveLabel(label)}
                  >
                    {label} ×
                  </Badge>
                ))}
              </div>
            )}
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
                  {isEditing ? 'Saving...' : 'Submitting...'}
                </>
              ) : (
                isEditing ? 'Save Changes' : 'Submit Request'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

