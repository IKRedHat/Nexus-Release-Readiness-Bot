/**
 * User Management Page
 * 
 * Admin interface for managing users and role assignments.
 * Requires VIEW_USERS, CREATE_USER, EDIT_USER, DELETE_USER, ASSIGN_ROLES permissions.
 */

import React, { useState, useEffect } from 'react';
import {
  Users, UserPlus, Search, Filter, MoreVertical,
  Mail, Shield, Calendar, Check, X, Edit2, Trash2,
  ChevronDown, AlertCircle, Loader2, RefreshCw
} from 'lucide-react';

interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  roles: string[];
  status: 'active' | 'inactive' | 'pending' | 'suspended';
  sso_provider: string;
  department?: string;
  title?: string;
  created_at: string;
  last_login?: string;
}

interface Role {
  id: string;
  name: string;
  description?: string;
  is_system_role: boolean;
}

// Auto-detect API URL based on environment
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  if (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')) {
    return 'https://nexus-admin-api-63b4.onrender.com';
  }
  return 'http://localhost:8088';
};
const API_URL = getApiUrl();

const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('nexus_access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const statusColors: Record<string, string> = {
  active: 'bg-green-500/20 text-green-400 border-green-500/30',
  inactive: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  suspended: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [actionMenuOpen, setActionMenuOpen] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    roles: [] as string[],
    department: '',
    title: '',
  });
  
  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, []);
  
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/users`, {
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) throw new Error('Failed to fetch users');
      
      const data = await response.json();
      setUsers(data.users || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchRoles = async () => {
    try {
      const response = await fetch(`${API_URL}/roles`, {
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) throw new Error('Failed to fetch roles');
      
      const data = await response.json();
      setRoles(data.roles || []);
    } catch (err) {
      console.error('Failed to fetch roles:', err);
    }
  };
  
  const handleCreateUser = async () => {
    try {
      const response = await fetch(`${API_URL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create user');
      }
      
      setShowCreateModal(false);
      setFormData({ email: '', name: '', roles: [], department: '', title: '' });
      fetchUsers();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
    }
  };
  
  const handleUpdateUser = async () => {
    if (!selectedUser) return;
    
    try {
      const response = await fetch(`${API_URL}/users/${selectedUser.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          name: formData.name,
          roles: formData.roles,
          department: formData.department,
          title: formData.title,
        }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to update user');
      }
      
      setShowEditModal(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
    }
  };
  
  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    try {
      const response = await fetch(`${API_URL}/users/${userId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete user');
      }
      
      fetchUsers();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete user');
    }
  };
  
  const handleRoleToggle = (roleId: string) => {
    setFormData(prev => ({
      ...prev,
      roles: prev.roles.includes(roleId)
        ? prev.roles.filter(r => r !== roleId)
        : [...prev.roles, roleId],
    }));
  };
  
  const openEditModal = (user: User) => {
    setSelectedUser(user);
    setFormData({
      email: user.email,
      name: user.name,
      roles: user.roles,
      department: user.department || '',
      title: user.title || '',
    });
    setShowEditModal(true);
    setActionMenuOpen(null);
  };
  
  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = !statusFilter || user.status === statusFilter;
    return matchesSearch && matchesStatus;
  });
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-cyber-accent" />
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Users className="w-7 h-7 text-cyber-accent" />
            User Management
          </h1>
          <p className="text-gray-400 mt-1">Manage users and their role assignments</p>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={fetchUsers}
            className="p-2 bg-cyber-dark border border-cyber-border rounded-lg hover:border-cyber-accent transition-colors"
          >
            <RefreshCw className="w-5 h-5 text-gray-400" />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-cyber-accent text-cyber-dark font-medium rounded-lg hover:bg-cyber-accent-light transition-colors"
          >
            <UserPlus className="w-5 h-5" />
            Add User
          </button>
        </div>
      </div>
      
      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      
      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search users..."
            className="w-full pl-10 pr-4 py-2 bg-cyber-dark border border-cyber-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyber-accent"
          />
        </div>
        
        <div className="relative">
          <button
            onClick={() => setStatusFilter(statusFilter ? null : 'active')}
            className="flex items-center gap-2 px-4 py-2 bg-cyber-dark border border-cyber-border rounded-lg text-gray-300 hover:border-cyber-accent"
          >
            <Filter className="w-5 h-5" />
            {statusFilter || 'All Status'}
            <ChevronDown className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Users Table */}
      <div className="bg-cyber-dark border border-cyber-border rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-cyber-border">
              <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">User</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Roles</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Status</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Last Login</th>
              <th className="px-6 py-4 text-right text-sm font-medium text-gray-400">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-cyber-border">
            {filteredUsers.map(user => (
              <tr key={user.id} className="hover:bg-cyber-darker/50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-cyber-accent/20 rounded-full flex items-center justify-center">
                      {user.avatar_url ? (
                        <img src={user.avatar_url} alt={user.name} className="w-10 h-10 rounded-full" />
                      ) : (
                        <span className="text-cyber-accent font-medium">
                          {user.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                        </span>
                      )}
                    </div>
                    <div>
                      <div className="text-white font-medium">{user.name}</div>
                      <div className="text-gray-400 text-sm flex items-center gap-1">
                        <Mail className="w-3 h-3" />
                        {user.email}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1">
                    {user.roles.map(roleId => {
                      const role = roles.find(r => r.id === roleId);
                      return (
                        <span
                          key={roleId}
                          className="px-2 py-1 bg-purple-500/20 text-purple-400 text-xs rounded-full border border-purple-500/30"
                        >
                          {role?.name || roleId}
                        </span>
                      );
                    })}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-3 py-1 text-xs rounded-full border ${statusColors[user.status]}`}>
                    {user.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-400 text-sm">
                  {user.last_login ? (
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {new Date(user.last_login).toLocaleDateString()}
                    </div>
                  ) : (
                    'Never'
                  )}
                </td>
                <td className="px-6 py-4">
                  <div className="flex justify-end relative">
                    <button
                      onClick={() => setActionMenuOpen(actionMenuOpen === user.id ? null : user.id)}
                      className="p-2 hover:bg-cyber-darker rounded-lg"
                    >
                      <MoreVertical className="w-5 h-5 text-gray-400" />
                    </button>
                    
                    {actionMenuOpen === user.id && (
                      <div className="absolute right-0 top-10 w-48 bg-cyber-darker border border-cyber-border rounded-lg shadow-xl z-10">
                        <button
                          onClick={() => openEditModal(user)}
                          className="w-full px-4 py-2 text-left text-gray-300 hover:bg-cyber-dark flex items-center gap-2"
                        >
                          <Edit2 className="w-4 h-4" />
                          Edit User
                        </button>
                        <button
                          onClick={() => {
                            handleDeleteUser(user.id);
                            setActionMenuOpen(null);
                          }}
                          className="w-full px-4 py-2 text-left text-red-400 hover:bg-cyber-dark flex items-center gap-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          Delete User
                        </button>
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredUsers.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No users found</p>
          </div>
        )}
      </div>
      
      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-cyber-dark border border-cyber-border rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <UserPlus className="w-6 h-6 text-cyber-accent" />
              Create New User
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={e => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                  placeholder="user@company.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                  placeholder="John Doe"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Department</label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={e => setFormData({ ...formData, department: e.target.value })}
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                  placeholder="Engineering"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={e => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                  placeholder="Software Engineer"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Roles</label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {roles.map(role => (
                    <label key={role.id} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.roles.includes(role.id)}
                        onChange={() => handleRoleToggle(role.id)}
                        className="w-4 h-4 rounded border-cyber-border bg-cyber-darker text-cyber-accent focus:ring-cyber-accent"
                      />
                      <span className="text-gray-300">{role.name}</span>
                      {role.is_system_role && (
                        <Shield className="w-3 h-3 text-gray-500" />
                      )}
                    </label>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-gray-300 hover:border-gray-500"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateUser}
                className="flex-1 px-4 py-2 bg-cyber-accent text-cyber-dark font-medium rounded-lg hover:bg-cyber-accent-light flex items-center justify-center gap-2"
              >
                <Check className="w-4 h-4" />
                Create User
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-cyber-dark border border-cyber-border rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Edit2 className="w-6 h-6 text-cyber-accent" />
              Edit User
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  disabled
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-gray-500 cursor-not-allowed"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Department</label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={e => setFormData({ ...formData, department: e.target.value })}
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={e => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Roles</label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {roles.map(role => (
                    <label key={role.id} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.roles.includes(role.id)}
                        onChange={() => handleRoleToggle(role.id)}
                        className="w-4 h-4 rounded border-cyber-border bg-cyber-darker text-cyber-accent focus:ring-cyber-accent"
                      />
                      <span className="text-gray-300">{role.name}</span>
                      {role.is_system_role && (
                        <Shield className="w-3 h-3 text-gray-500" />
                      )}
                    </label>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setSelectedUser(null);
                }}
                className="flex-1 px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-gray-300 hover:border-gray-500"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateUser}
                className="flex-1 px-4 py-2 bg-cyber-accent text-cyber-dark font-medium rounded-lg hover:bg-cyber-accent-light flex items-center justify-center gap-2"
              >
                <Check className="w-4 h-4" />
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;

