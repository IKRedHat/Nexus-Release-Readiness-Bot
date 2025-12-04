'use client';

import { useUsers } from '@/hooks/useAPI';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Layout from '@/components/Layout';
import { Users, Plus, Edit, Trash2, AlertCircle, Shield } from 'lucide-react';
import { formatRelativeTime } from '@/lib/utils';
import type { User } from '@/types';

export default function UserManagementPage() {
  const { data: users, error, isLoading } = useUsers();

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-8">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-96" />
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
              <h2 className="text-2xl font-bold mb-2">Unable to Load Users</h2>
              <Button onClick={() => window.location.reload()}>Retry</Button>
            </div>
          </CardContent>
        </Card>
      </Layout>
    );
  }

  const usersList = users || [];

  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold">User Management</h1>
            <p className="text-muted-foreground">Manage users, roles, and permissions</p>
          </div>
          <Button><Plus size={16} className="mr-2" /> Add User</Button>
        </div>

        {usersList.length > 0 ? (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-border">
                  <tr>
                    <th className="text-left p-4 font-semibold">User</th>
                    <th className="text-left p-4 font-semibold">Roles</th>
                    <th className="text-left p-4 font-semibold">Status</th>
                    <th className="text-left p-4 font-semibold">Last Login</th>
                    <th className="text-right p-4 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {usersList.map((user: User) => (
                    <tr key={user.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <span className="font-semibold text-primary">
                              {user.name?.charAt(0) || user.email.charAt(0)}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium">{user.name || user.email}</p>
                            <p className="text-sm text-muted-foreground">{user.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1">
                          {user.roles.map((role, i) => (
                            <Badge key={i} variant="outline">
                              {role}
                            </Badge>
                          ))}
                          {user.is_admin && (
                            <Badge className="bg-primary">
                              <Shield size={12} className="mr-1" />
                              Admin
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        <Badge variant={user.is_active ? 'default' : 'outline'}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                      <td className="p-4 text-sm text-muted-foreground">
                        {user.last_login ? formatRelativeTime(user.last_login) : 'Never'}
                      </td>
                      <td className="p-4">
                        <div className="flex items-center justify-end gap-2">
                          <Button size="sm" variant="ghost">
                            <Edit size={16} />
                          </Button>
                          <Button size="sm" variant="ghost" className="text-destructive">
                            <Trash2 size={16} />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        ) : (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <Users className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Users Found</h3>
                <Button><Plus size={16} className="mr-2" /> Add First User</Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}

