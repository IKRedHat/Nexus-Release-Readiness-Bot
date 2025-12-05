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
import type { User, Role } from '@/types';

export interface UserFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user?: User | null;
  roles: Role[];
  onSubmit: (data: UserFormData) => Promise<void>;
}

export interface UserFormData {
  name: string;
  email: string;
  password?: string;
  roles: string[];
  is_active: boolean;
}

const initialFormData: UserFormData = {
  name: '',
  email: '',
  password: '',
  roles: ['user'],
  is_active: true,
};

/**
 * UserFormDialog Component
 * 
 * Dialog for creating and editing users.
 */
export function UserFormDialog({
  open,
  onOpenChange,
  user,
  roles,
  onSubmit,
}: UserFormDialogProps) {
  const [formData, setFormData] = useState<UserFormData>(initialFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof UserFormData, string>>>({});

  const isEditing = !!user;

  useEffect(() => {
    if (open) {
      if (user) {
        setFormData({
          name: user.name || '',
          email: user.email,
          password: '',
          roles: user.roles,
          is_active: user.is_active,
        });
      } else {
        setFormData(initialFormData);
      }
      setErrors({});
    }
  }, [open, user]);

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof UserFormData, string>> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!isEditing && !formData.password) {
      newErrors.password = 'Password is required for new users';
    } else if (formData.password && formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (formData.roles.length === 0) {
      newErrors.roles = 'At least one role is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const submitData = { ...formData };
      if (isEditing && !submitData.password) {
        delete submitData.password;
      }
      await onSubmit(submitData);
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to save user:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleRole = (roleName: string) => {
    setFormData(prev => ({
      ...prev,
      roles: prev.roles.includes(roleName)
        ? prev.roles.filter(r => r !== roleName)
        : [...prev.roles, roleName],
    }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit User' : 'Add New User'}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update user details and permissions.'
              : 'Create a new user account with assigned roles.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Full Name <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="John Doe"
              disabled={isSubmitting}
            />
            {errors.name && (
              <p className="text-sm text-red-500">{errors.name}</p>
            )}
          </div>

          {/* Email */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Email <span className="text-red-500">*</span>
            </label>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              placeholder="john@example.com"
              disabled={isSubmitting}
            />
            {errors.email && (
              <p className="text-sm text-red-500">{errors.email}</p>
            )}
          </div>

          {/* Password */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Password {!isEditing && <span className="text-red-500">*</span>}
            </label>
            <Input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
              placeholder={isEditing ? 'Leave blank to keep current' : 'Enter password'}
              disabled={isSubmitting}
            />
            {errors.password && (
              <p className="text-sm text-red-500">{errors.password}</p>
            )}
            {isEditing && (
              <p className="text-xs text-muted-foreground">
                Leave blank to keep the current password.
              </p>
            )}
          </div>

          {/* Roles */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Roles <span className="text-red-500">*</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {roles.map((role) => (
                <Badge
                  key={role.id}
                  variant={formData.roles.includes(role.name) ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => !isSubmitting && toggleRole(role.name)}
                >
                  {role.name}
                </Badge>
              ))}
            </div>
            {errors.roles && (
              <p className="text-sm text-red-500">{errors.roles}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Click to toggle roles. Selected roles are highlighted.
            </p>
          </div>

          {/* Active Status */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              disabled={isSubmitting}
              className="w-4 h-4 rounded border-input"
            />
            <label htmlFor="is_active" className="text-sm font-medium text-foreground">
              Active Account
            </label>
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
                isEditing ? 'Save Changes' : 'Create User'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

