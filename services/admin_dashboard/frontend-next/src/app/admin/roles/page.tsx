'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { useRoles, usePermissions, mutateAPI } from '@/hooks/useAPI';
import { DataPage } from '@/components/page';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ConfirmDialog, useConfirmDialog } from '@/components/ui/confirm-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Shield, Plus, Edit, Trash2, Lock, Loader2 } from 'lucide-react';
import { endpoints } from '@/lib/api';
import type { Role, Permission } from '@/types';

interface RoleFormData {
  name: string;
  description: string;
  permissions: string[];
}

const initialFormData: RoleFormData = {
  name: '',
  description: '',
  permissions: [],
};

/**
 * Role Form Dialog
 */
function RoleFormDialog({
  open,
  onOpenChange,
  role,
  permissions,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  role: Role | null;
  permissions: Permission[];
  onSubmit: (data: RoleFormData) => Promise<void>;
}) {
  const [formData, setFormData] = useState<RoleFormData>(initialFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof RoleFormData, string>>>({});
  
  const isEditing = !!role;

  // Group permissions by category
  const permissionsByCategory = permissions.reduce((acc, perm) => {
    const category = (perm as any).category || 'Other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(perm);
    return acc;
  }, {} as Record<string, Permission[]>);

  // Reset form when dialog opens
  useState(() => {
    if (open) {
      if (role) {
        setFormData({
          name: role.name,
          description: role.description,
          permissions: role.permissions,
        });
      } else {
        setFormData(initialFormData);
      }
      setErrors({});
    }
  });

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof RoleFormData, string>> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Role name is required';
    } else if (!/^[a-z_]+$/.test(formData.name)) {
      newErrors.name = 'Role name must be lowercase with underscores only';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (formData.permissions.length === 0) {
      newErrors.permissions = 'At least one permission is required';
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
      console.error('Failed to save role:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const togglePermission = (permName: string) => {
    setFormData(prev => ({
      ...prev,
      permissions: prev.permissions.includes(permName)
        ? prev.permissions.filter(p => p !== permName)
        : [...prev.permissions, permName],
    }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Role' : 'Create New Role'}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the role name, description, and permissions.'
              : 'Create a new role with specific permissions.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Role Name <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value.toLowerCase() }))}
              placeholder="e.g., developer, qa_engineer"
              disabled={isSubmitting || (isEditing && role?.is_system)}
            />
            {errors.name && <p className="text-sm text-red-500">{errors.name}</p>}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Description <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Describe what this role is for"
              disabled={isSubmitting}
            />
            {errors.description && <p className="text-sm text-red-500">{errors.description}</p>}
          </div>

          {/* Permissions */}
          <div className="space-y-4">
            <label className="text-sm font-medium">
              Permissions <span className="text-red-500">*</span>
            </label>
            {Object.entries(permissionsByCategory).map(([category, perms]) => (
              <div key={category} className="space-y-2">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase">{category}</h4>
                <div className="flex flex-wrap gap-2">
                  {perms.map((perm) => (
                    <Badge
                      key={perm.id}
                      variant={formData.permissions.includes(perm.name) ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => !isSubmitting && togglePermission(perm.name)}
                    >
                      {perm.name}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
            {errors.permissions && <p className="text-sm text-red-500">{errors.permissions}</p>}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {isEditing ? 'Saving...' : 'Creating...'}
                </>
              ) : (
                isEditing ? 'Save Changes' : 'Create Role'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Role card component
 */
function RoleCard({ 
  role, 
  isSystem = false,
  onEdit,
  onDelete,
}: { 
  role: Role; 
  isSystem?: boolean;
  onEdit: (role: Role) => void;
  onDelete: (role: Role) => void;
}) {
  return (
    <Card className={!isSystem ? 'hover:shadow-lg transition-shadow' : ''}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
              isSystem ? 'bg-primary/10' : 'bg-purple-500/10'
            }`}>
              <Shield className={`w-6 h-6 ${isSystem ? 'text-primary' : 'text-purple-500'}`} />
            </div>
            <div>
              <h3 className="font-semibold text-lg">{role.name}</h3>
              <p className="text-sm text-muted-foreground">{role.description}</p>
            </div>
          </div>
          {isSystem && <Badge variant="outline">System</Badge>}
        </div>
        <div className="space-y-3">
          <div>
            <p className="text-xs text-muted-foreground mb-2">
              Permissions ({role.permissions.length})
            </p>
            <div className="flex flex-wrap gap-1">
              {role.permissions.slice(0, 6).map((perm, i) => (
                <Badge key={i} variant="outline" className="text-xs">{perm}</Badge>
              ))}
              {role.permissions.length > 6 && (
                <Badge variant="outline" className="text-xs">+{role.permissions.length - 6}</Badge>
              )}
            </div>
          </div>
          {role.user_count !== undefined && (
            <div className="text-sm text-muted-foreground">
              {role.user_count} user{role.user_count !== 1 ? 's' : ''}
            </div>
          )}
          {!isSystem && (
            <div className="flex gap-2 pt-2 border-t border-border">
              <Button size="sm" variant="outline" className="flex-1" onClick={() => onEdit(role)}>
                <Edit size={14} className="mr-1" />
                Edit
              </Button>
              <Button 
                size="sm" 
                variant="outline" 
                className="flex-1 text-destructive hover:bg-destructive/10"
                onClick={() => onDelete(role)}
              >
                <Trash2 size={14} className="mr-1" />
                Delete
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Empty custom roles component
 */
function EmptyCustomRoles({ onCreate }: { onCreate: () => void }) {
  return (
    <Card>
      <CardContent className="py-12">
        <div className="text-center">
          <Shield className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">No Custom Roles</h3>
          <p className="text-muted-foreground mb-6">Create custom roles with specific permissions</p>
          <Button onClick={onCreate}>
            <Plus size={16} className="mr-2" />
            Create Role
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Roles content component
 */
function RolesContent({ 
  roles, 
  onCreate,
  onEdit,
  onDelete,
}: { 
  roles: Role[];
  onCreate: () => void;
  onEdit: (role: Role) => void;
  onDelete: (role: Role) => void;
}) {
  const systemRoles = roles.filter(r => r.is_system);
  const customRoles = roles.filter(r => !r.is_system);

  return (
    <div className="space-y-8">
      {/* System Roles */}
      {systemRoles.length > 0 && (
        <div>
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <Lock size={20} />
            System Roles
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {systemRoles.map((role: Role) => (
              <RoleCard 
                key={role.id} 
                role={role} 
                isSystem 
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </div>
        </div>
      )}

      {/* Custom Roles */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Custom Roles</h2>
        {customRoles.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {customRoles.map((role: Role) => (
              <RoleCard 
                key={role.id} 
                role={role}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </div>
        ) : (
          <EmptyCustomRoles onCreate={onCreate} />
        )}
      </div>
    </div>
  );
}

/**
 * Role management page with full CRUD functionality
 */
export default function RoleManagementPage() {
  const { data: roles, error, isLoading, mutate } = useRoles();
  const { data: permissions } = usePermissions();
  
  // Form dialog state
  const [formOpen, setFormOpen] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  
  // Delete confirmation state
  const deleteConfirm = useConfirmDialog<Role>();

  // Open create dialog
  const handleCreate = () => {
    setSelectedRole(null);
    setFormOpen(true);
  };

  // Open edit dialog
  const handleEdit = (role: Role) => {
    setSelectedRole(role);
    setFormOpen(true);
  };

  // Handle form submission
  const handleFormSubmit = async (data: RoleFormData) => {
    try {
      if (selectedRole) {
        await mutateAPI(`${endpoints.roles}/${selectedRole.id}`, 'PUT', data);
        toast.success('Role Updated', {
          description: `Role "${data.name}" has been updated successfully.`,
        });
      } else {
        await mutateAPI(endpoints.roles, 'POST', data);
        toast.success('Role Created', {
          description: `Role "${data.name}" has been created successfully.`,
        });
      }
      mutate();
    } catch (error: any) {
      toast.error('Operation Failed', {
        description: error.response?.data?.detail || 'Failed to save role.',
      });
      throw error;
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (!deleteConfirm.item) return;
    
    try {
      await mutateAPI(`${endpoints.roles}/${deleteConfirm.item.id}`, 'DELETE');
      toast.success('Role Deleted', {
        description: `Role "${deleteConfirm.item.name}" has been deleted.`,
      });
      mutate();
    } catch (error: any) {
      toast.error('Delete Failed', {
        description: error.response?.data?.detail || 'Failed to delete role.',
      });
      throw error;
    }
  };

  return (
    <>
      <DataPage
        title="Role Management"
        description="Manage roles and permissions"
        isLoading={isLoading}
        error={error}
        data={roles}
        onRetry={mutate}
        errorMessage="Could not fetch roles from the backend API."
        loadingLayout="grid"
        loadingCount={4}
        actions={
          <Button onClick={handleCreate}>
            <Plus size={16} className="mr-2" />
            Create Role
          </Button>
        }
      >
        {(rolesList) => (
          <RolesContent 
            roles={rolesList}
            onCreate={handleCreate}
            onEdit={handleEdit}
            onDelete={deleteConfirm.openConfirm}
          />
        )}
      </DataPage>

      {/* Create/Edit Dialog */}
      <RoleFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        role={selectedRole}
        permissions={permissions || []}
        onSubmit={handleFormSubmit}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteConfirm.isOpen}
        onOpenChange={deleteConfirm.setIsOpen}
        title="Delete Role"
        description={`Are you sure you want to delete the "${deleteConfirm.item?.name}" role? Users with this role will lose associated permissions.`}
        variant="danger"
        confirmText="Delete Role"
        onConfirm={handleDelete}
      />
    </>
  );
}
