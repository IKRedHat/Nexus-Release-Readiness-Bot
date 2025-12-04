'use client';

import { useRoles } from '@/hooks/useAPI';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Layout from '@/components/Layout';
import { Shield, Plus, Edit, Trash2, AlertCircle, Lock } from 'lucide-react';
import type { Role } from '@/types';

export default function RoleManagementPage() {
  const { data: roles, error, isLoading } = useRoles();

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-8">
          <Skeleton className="h-10 w-48" />
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
              <h2 className="text-2xl font-bold mb-2">Unable to Load Roles</h2>
              <Button onClick={() => window.location.reload()}>Retry</Button>
            </div>
          </CardContent>
        </Card>
      </Layout>
    );
  }

  const rolesList = roles || [];
  const systemRoles = rolesList.filter((r: Role) => r.is_system);
  const customRoles = rolesList.filter((r: Role) => !r.is_system);

  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold">Role Management</h1>
            <p className="text-muted-foreground">Manage roles and permissions</p>
          </div>
          <Button><Plus size={16} className="mr-2" /> Create Role</Button>
        </div>

        {/* System Roles */}
        <div>
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <Lock size={20} />
            System Roles
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {systemRoles.map((role: Role) => (
              <Card key={role.id}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Shield className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">{role.name}</h3>
                        <p className="text-sm text-muted-foreground">{role.description}</p>
                      </div>
                    </div>
                    <Badge variant="outline">System</Badge>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">
                        Permissions ({role.permissions.length})
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {role.permissions.slice(0, 6).map((perm, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {perm}
                          </Badge>
                        ))}
                        {role.permissions.length > 6 && (
                          <Badge variant="outline" className="text-xs">
                            +{role.permissions.length - 6}
                          </Badge>
                        )}
                      </div>
                    </div>
                    {role.user_count !== undefined && (
                      <div className="text-sm text-muted-foreground">
                        {role.user_count} user{role.user_count !== 1 ? 's' : ''}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Custom Roles */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">Custom Roles</h2>
          {customRoles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {customRoles.map((role: Role) => (
                <Card key={role.id} className="hover:shadow-lg transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
                          <Shield className="w-6 h-6 text-purple-500" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg">{role.name}</h3>
                          <p className="text-sm text-muted-foreground">{role.description}</p>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <p className="text-xs text-muted-foreground mb-2">
                          Permissions ({role.permissions.length})
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {role.permissions.slice(0, 6).map((perm, i) => (
                            <Badge key={i} variant="outline" className="text-xs">
                              {perm}
                            </Badge>
                          ))}
                          {role.permissions.length > 6 && (
                            <Badge variant="outline" className="text-xs">
                              +{role.permissions.length - 6}
                            </Badge>
                          )}
                        </div>
                      </div>
                      {role.user_count !== undefined && (
                        <div className="text-sm text-muted-foreground">
                          {role.user_count} user{role.user_count !== 1 ? 's' : ''}
                        </div>
                      )}
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
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center">
                  <Shield className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">No Custom Roles</h3>
                  <p className="text-muted-foreground mb-6">
                    Create custom roles with specific permissions
                  </p>
                  <Button><Plus size={16} className="mr-2" /> Create Role</Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </Layout>
  );
}

