'use client';

import { useRoles } from '@/hooks/useAPI';
import { DataPage } from '@/components/page';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Shield, Plus, Edit, Trash2, Lock } from 'lucide-react';
import type { Role } from '@/types';

/**
 * Role card component
 */
function RoleCard({ role, isSystem = false }: { role: Role; isSystem?: boolean }) {
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
              <Button size="sm" variant="outline" className="flex-1">
                <Edit size={14} className="mr-1" />
                Edit
              </Button>
              <Button size="sm" variant="outline" className="flex-1 text-destructive">
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
function EmptyCustomRoles() {
  return (
    <Card>
      <CardContent className="py-12">
        <div className="text-center">
          <Shield className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">No Custom Roles</h3>
          <p className="text-muted-foreground mb-6">Create custom roles with specific permissions</p>
          <Button>
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
function RolesContent({ roles }: { roles: Role[] }) {
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
              <RoleCard key={role.id} role={role} isSystem />
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
              <RoleCard key={role.id} role={role} />
            ))}
          </div>
        ) : (
          <EmptyCustomRoles />
        )}
      </div>
    </div>
  );
}

/**
 * Role management page - refactored to use DataPage
 */
export default function RoleManagementPage() {
  const { data: roles, error, isLoading, mutate } = useRoles();

  return (
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
        <Button>
          <Plus size={16} className="mr-2" />
          Create Role
        </Button>
      }
    >
      {(rolesList) => <RolesContent roles={rolesList} />}
    </DataPage>
  );
}
