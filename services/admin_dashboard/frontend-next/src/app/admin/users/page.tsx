'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { useUsers, useRoles, mutateAPI } from '@/hooks/useAPI';
import { DataPage } from '@/components/page';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ConfirmDialog, useConfirmDialog } from '@/components/ui/confirm-dialog';
import { UserFormDialog, UserFormData } from '@/components/users/UserFormDialog';
import { Users, Plus, Edit, Trash2, Shield, Search } from 'lucide-react';
import { formatRelativeTime, filterBySearch } from '@/lib/utils';
import { endpoints } from '@/lib/api';
import type { User } from '@/types';

/**
 * Empty state component
 */
function EmptyUsers({ onCreate }: { onCreate: () => void }) {
  return (
    <Card>
      <CardContent className="py-12">
        <div className="text-center">
          <Users className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">No Users Found</h3>
          <Button onClick={onCreate}>
            <Plus size={16} className="mr-2" />
            Add First User
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * User stats cards
 */
function UserStats({ users }: { users: User[] }) {
  const stats = [
    { label: 'Total Users', value: users.length },
    { label: 'Active Users', value: users.filter(u => u.is_active).length },
    { label: 'Admins', value: users.filter(u => u.is_admin).length },
    { label: 'Inactive', value: users.filter(u => !u.is_active).length },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {stats.map(stat => (
        <Card key={stat.label}>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/**
 * User table row
 */
function UserRow({ 
  user, 
  onEdit, 
  onDelete 
}: { 
  user: User; 
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
}) {
  return (
    <tr className="border-b border-border last:border-0 hover:bg-muted/50">
      <td className="p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
            <span className="font-semibold text-primary">
              {user.name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <p className="font-medium">{user.name || 'Unnamed User'}</p>
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
          <Button 
            size="sm" 
            variant="ghost"
            onClick={() => onEdit(user)}
          >
            <Edit size={16} />
          </Button>
          <Button 
            size="sm" 
            variant="ghost" 
            className="text-destructive"
            onClick={() => onDelete(user)}
          >
            <Trash2 size={16} />
          </Button>
        </div>
      </td>
    </tr>
  );
}

/**
 * Users table
 */
function UsersTable({ 
  users, 
  onEdit, 
  onDelete 
}: { 
  users: User[]; 
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
}) {
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
              <UserRow 
                key={user.id} 
                user={user} 
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/**
 * User management page with full CRUD functionality
 */
export default function UserManagementPage() {
  const { data: users, error, isLoading, mutate } = useUsers();
  const { data: roles } = useRoles();
  
  // Search state
  const [search, setSearch] = useState('');
  
  // Form dialog state
  const [formOpen, setFormOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  
  // Delete confirmation state
  const deleteConfirm = useConfirmDialog<User>();

  // Filter users by search
  const filteredUsers = users 
    ? filterBySearch(users, search, ['name', 'email'])
    : [];

  // Open create dialog
  const handleCreate = () => {
    setSelectedUser(null);
    setFormOpen(true);
  };

  // Open edit dialog
  const handleEdit = (user: User) => {
    setSelectedUser(user);
    setFormOpen(true);
  };

  // Handle form submission
  const handleFormSubmit = async (data: UserFormData) => {
    try {
      if (selectedUser) {
        await mutateAPI(
          `${endpoints.users}/${selectedUser.id}`,
          'PUT',
          data
        );
        toast.success('User Updated', {
          description: `${data.name} has been updated successfully.`,
        });
      } else {
        await mutateAPI(endpoints.users, 'POST', data);
        toast.success('User Created', {
          description: `${data.name} has been created successfully.`,
        });
      }
      mutate();
    } catch (error: any) {
      toast.error('Operation Failed', {
        description: error.response?.data?.detail || 'Failed to save user.',
      });
      throw error;
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (!deleteConfirm.item) return;
    
    try {
      await mutateAPI(`${endpoints.users}/${deleteConfirm.item.id}`, 'DELETE');
      toast.success('User Deleted', {
        description: `${deleteConfirm.item.name || deleteConfirm.item.email} has been deleted.`,
      });
      mutate();
    } catch (error: any) {
      toast.error('Delete Failed', {
        description: error.response?.data?.detail || 'Failed to delete user.',
      });
      throw error;
    }
  };

  return (
    <>
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
        emptyState={<EmptyUsers onCreate={handleCreate} />}
        actions={
          <Button onClick={handleCreate}>
            <Plus size={16} className="mr-2" />
            Add User
          </Button>
        }
      >
        {(usersList) => (
          <div className="space-y-6">
            <UserStats users={usersList} />
            
            {/* Search */}
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search users by name or email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            
            {filteredUsers.length > 0 ? (
              <UsersTable 
                users={filteredUsers}
                onEdit={handleEdit}
                onDelete={deleteConfirm.openConfirm}
              />
            ) : search ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground">
                    No users found matching "{search}"
                  </p>
                </CardContent>
              </Card>
            ) : (
              <EmptyUsers onCreate={handleCreate} />
            )}
          </div>
        )}
      </DataPage>

      {/* Create/Edit Dialog */}
      <UserFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        user={selectedUser}
        roles={roles || []}
        onSubmit={handleFormSubmit}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteConfirm.isOpen}
        onOpenChange={deleteConfirm.setIsOpen}
        title="Delete User"
        description={`Are you sure you want to delete "${deleteConfirm.item?.name || deleteConfirm.item?.email}"? This action cannot be undone.`}
        variant="danger"
        confirmText="Delete User"
        onConfirm={handleDelete}
      />
    </>
  );
}
