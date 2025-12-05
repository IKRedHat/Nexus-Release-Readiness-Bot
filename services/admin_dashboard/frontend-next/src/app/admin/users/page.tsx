'use client';

import { useUsers } from '@/hooks/useAPI';
import { DataPage } from '@/components/page';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Users, Plus, Edit, Trash2, Shield } from 'lucide-react';
import { formatRelativeTime } from '@/lib/utils';
import type { User } from '@/types';

/**
 * Empty state component
 */
function EmptyUsers() {
  return (
    <Card>
      <CardContent className="py-12">
        <div className="text-center">
          <Users className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">No Users Found</h3>
          <Button>
            <Plus size={16} className="mr-2" />
            Add First User
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * User table row
 */
function UserRow({ user }: { user: User }) {
  return (
    <tr className="border-b border-border last:border-0 hover:bg-muted/50">
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
            <Badge key={i} variant="outline">{role}</Badge>
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
          <Button size="sm" variant="ghost"><Edit size={16} /></Button>
          <Button size="sm" variant="ghost" className="text-destructive"><Trash2 size={16} /></Button>
        </div>
      </td>
    </tr>
  );
}

/**
 * Users table
 */
function UsersTable({ users }: { users: User[] }) {
  return (
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
            {users.map((user: User) => (
              <UserRow key={user.id} user={user} />
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/**
 * User management page - refactored to use DataPage
 */
export default function UserManagementPage() {
  const { data: users, error, isLoading, mutate } = useUsers();

  return (
    <DataPage
      title="User Management"
      description="Manage users, roles, and permissions"
      isLoading={isLoading}
      error={error}
      data={users}
      onRetry={mutate}
      errorMessage="Could not fetch users from the backend API."
      loadingLayout="list"
      loadingCount={1}
      emptyState={<EmptyUsers />}
      actions={
        <Button>
          <Plus size={16} className="mr-2" />
          Add User
        </Button>
      }
    >
      {(usersList) => <UsersTable users={usersList} />}
    </DataPage>
  );
}
