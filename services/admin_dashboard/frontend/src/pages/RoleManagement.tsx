/**
 * Role Management Page
 * 
 * Admin interface for managing dynamic roles and permissions.
 * Admins can create custom roles with specific permission sets.
 */

import React, { useState, useEffect } from 'react';
import {
  Shield, Plus, Search, MoreVertical,
  Check, X, Edit2, Trash2, Lock,
  ChevronDown, ChevronUp, AlertCircle, Loader2, RefreshCw,
  Copy
} from 'lucide-react';

interface Permission {
  id: string;
  name: string;
  category: string;
}

interface Role {
  id: string;
  name: string;
  description?: string;
  permissions: string[];
  is_system_role: boolean;
  is_default: boolean;
  created_at: string;
  created_by?: string;
}

// Auto-detect API URL based on environment
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  if (typeof window !== 'undefined' && 
      (window.location.hostname.includes('vercel.app') || 
       window.location.hostname.includes('nexus-admin-dashboard'))) {
    return 'https://nexus-admin-api-63b4.onrender.com';
  }
  return 'http://localhost:8088';
};
const API_URL = getApiUrl();

const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('nexus_access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const categoryColors: Record<string, string> = {
  dashboard: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  config: 'bg-green-500/20 text-green-400 border-green-500/30',
  agents: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  releases: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  users: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  roles: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  features: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  observability: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  api: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
  system: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export const RoleManagement: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [, setPermissions] = useState<Permission[]>([]);
  const [permissionCategories, setPermissionCategories] = useState<Record<string, Permission[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [expandedRole, setExpandedRole] = useState<string | null>(null);
  const [actionMenuOpen, setActionMenuOpen] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissions: [] as string[],
    is_default: false,
  });
  
  useEffect(() => {
    fetchRoles();
    fetchPermissions();
  }, []);
  
  const fetchRoles = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/roles`, {
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) throw new Error('Failed to fetch roles');
      
      const data = await response.json();
      setRoles(data.roles || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load roles');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchPermissions = async () => {
    try {
      const response = await fetch(`${API_URL}/roles/permissions`, {
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) throw new Error('Failed to fetch permissions');
      
      const data = await response.json();
      setPermissions(data.permissions || []);
      setPermissionCategories(data.categories || {});
    } catch (err) {
      console.error('Failed to fetch permissions:', err);
    }
  };
  
  const handleCreateRole = async () => {
    try {
      const response = await fetch(`${API_URL}/roles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create role');
      }
      
      setShowCreateModal(false);
      setFormData({ name: '', description: '', permissions: [], is_default: false });
      fetchRoles();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create role');
    }
  };
  
  const handleUpdateRole = async () => {
    if (!selectedRole) return;
    
    try {
      const response = await fetch(`${API_URL}/roles/${selectedRole.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description,
          permissions: formData.permissions,
          is_default: formData.is_default,
        }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to update role');
      }
      
      setShowEditModal(false);
      setSelectedRole(null);
      fetchRoles();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update role');
    }
  };
  
  const handleDeleteRole = async (roleId: string) => {
    if (!confirm('Are you sure you want to delete this role? Users assigned this role will lose its permissions.')) return;
    
    try {
      const response = await fetch(`${API_URL}/roles/${roleId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete role');
      }
      
      fetchRoles();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete role');
    }
  };
  
  const handleDuplicateRole = (role: Role) => {
    setFormData({
      name: `${role.name} (Copy)`,
      description: role.description || '',
      permissions: [...role.permissions],
      is_default: false,
    });
    setShowCreateModal(true);
    setActionMenuOpen(null);
  };
  
  const handlePermissionToggle = (permissionId: string) => {
    setFormData(prev => ({
      ...prev,
      permissions: prev.permissions.includes(permissionId)
        ? prev.permissions.filter(p => p !== permissionId)
        : [...prev.permissions, permissionId],
    }));
  };
  
  const handleCategoryToggle = (category: string) => {
    const categoryPerms = permissionCategories[category]?.map(p => p.id) || [];
    const allSelected = categoryPerms.every(p => formData.permissions.includes(p));
    
    setFormData(prev => ({
      ...prev,
      permissions: allSelected
        ? prev.permissions.filter(p => !categoryPerms.includes(p))
        : [...new Set([...prev.permissions, ...categoryPerms])],
    }));
  };
  
  const openEditModal = (role: Role) => {
    setSelectedRole(role);
    setFormData({
      name: role.name,
      description: role.description || '',
      permissions: [...role.permissions],
      is_default: role.is_default,
    });
    setShowEditModal(true);
    setActionMenuOpen(null);
  };
  
  const filteredRoles = roles.filter(role => 
    role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    role.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
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
            <Shield className="w-7 h-7 text-cyber-accent" />
            Role Management
          </h1>
          <p className="text-gray-400 mt-1">Create and manage dynamic roles with custom permissions</p>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={fetchRoles}
            className="p-2 bg-cyber-dark border border-cyber-border rounded-lg hover:border-cyber-accent transition-colors"
          >
            <RefreshCw className="w-5 h-5 text-gray-400" />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-cyber-accent text-cyber-dark font-medium rounded-lg hover:bg-cyber-accent-light transition-colors"
          >
            <Plus className="w-5 h-5" />
            Create Role
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
      
      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          placeholder="Search roles..."
          className="w-full pl-10 pr-4 py-2 bg-cyber-dark border border-cyber-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyber-accent"
        />
      </div>
      
      {/* Roles Grid */}
      <div className="grid gap-4">
        {filteredRoles.map(role => (
          <div
            key={role.id}
            className="bg-cyber-dark border border-cyber-border rounded-xl overflow-hidden"
          >
            <div 
              className="p-5 flex items-center justify-between cursor-pointer hover:bg-cyber-darker/50"
              onClick={() => setExpandedRole(expandedRole === role.id ? null : role.id)}
            >
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-lg ${role.is_system_role ? 'bg-purple-500/20' : 'bg-cyber-accent/20'}`}>
                  {role.is_system_role ? (
                    <Lock className="w-6 h-6 text-purple-400" />
                  ) : (
                    <Shield className="w-6 h-6 text-cyber-accent" />
                  )}
                </div>
                
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold text-white">{role.name}</h3>
                    {role.is_system_role && (
                      <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded-full">
                        System
                      </span>
                    )}
                    {role.is_default && (
                      <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded-full">
                        Default
                      </span>
                    )}
                  </div>
                  <p className="text-gray-400 text-sm mt-1">
                    {role.description || 'No description'}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-white font-medium">{role.permissions.length}</div>
                  <div className="text-gray-400 text-sm">permissions</div>
                </div>
                
                <div className="relative">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setActionMenuOpen(actionMenuOpen === role.id ? null : role.id);
                    }}
                    className="p-2 hover:bg-cyber-darker rounded-lg"
                  >
                    <MoreVertical className="w-5 h-5 text-gray-400" />
                  </button>
                  
                  {actionMenuOpen === role.id && (
                    <div className="absolute right-0 top-10 w-48 bg-cyber-darker border border-cyber-border rounded-lg shadow-xl z-10">
                      {!role.is_system_role && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            openEditModal(role);
                          }}
                          className="w-full px-4 py-2 text-left text-gray-300 hover:bg-cyber-dark flex items-center gap-2"
                        >
                          <Edit2 className="w-4 h-4" />
                          Edit Role
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDuplicateRole(role);
                        }}
                        className="w-full px-4 py-2 text-left text-gray-300 hover:bg-cyber-dark flex items-center gap-2"
                      >
                        <Copy className="w-4 h-4" />
                        Duplicate
                      </button>
                      {!role.is_system_role && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteRole(role.id);
                            setActionMenuOpen(null);
                          }}
                          className="w-full px-4 py-2 text-left text-red-400 hover:bg-cyber-dark flex items-center gap-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          Delete Role
                        </button>
                      )}
                    </div>
                  )}
                </div>
                
                {expandedRole === role.id ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </div>
            </div>
            
            {/* Expanded Permissions */}
            {expandedRole === role.id && (
              <div className="px-5 pb-5 border-t border-cyber-border">
                <h4 className="text-sm font-medium text-gray-400 mt-4 mb-3">Permissions</h4>
                <div className="flex flex-wrap gap-2">
                  {role.permissions.map(perm => {
                    const category = perm.split(':')[0];
                    return (
                      <span
                        key={perm}
                        className={`px-3 py-1 text-xs rounded-full border ${categoryColors[category] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}
                      >
                        {perm}
                      </span>
                    );
                  })}
                  {role.permissions.length === 0 && (
                    <span className="text-gray-500 text-sm">No permissions assigned</span>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        
        {filteredRoles.length === 0 && (
          <div className="text-center py-12 text-gray-400 bg-cyber-dark border border-cyber-border rounded-xl">
            <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No roles found</p>
          </div>
        )}
      </div>
      
      {/* Create/Edit Role Modal */}
      {(showCreateModal || showEditModal) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto py-8">
          <div className="bg-cyber-dark border border-cyber-border rounded-xl p-6 w-full max-w-2xl mx-4">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              {showEditModal ? (
                <>
                  <Edit2 className="w-6 h-6 text-cyber-accent" />
                  Edit Role
                </>
              ) : (
                <>
                  <Plus className="w-6 h-6 text-cyber-accent" />
                  Create New Role
                </>
              )}
            </h2>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Role Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                    placeholder="e.g., Release Manager"
                  />
                </div>
                
                <div className="flex items-center">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_default}
                      onChange={e => setFormData({ ...formData, is_default: e.target.checked })}
                      className="w-4 h-4 rounded border-cyber-border bg-cyber-darker text-cyber-accent focus:ring-cyber-accent"
                    />
                    <span className="text-gray-300">Set as default role for new users</span>
                  </label>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent resize-none"
                  placeholder="Describe what this role is for..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Permissions ({formData.permissions.length} selected)
                </label>
                <div className="space-y-4 max-h-80 overflow-y-auto pr-2">
                  {Object.entries(permissionCategories).map(([category, categoryPerms]) => {
                    const selectedCount = categoryPerms.filter(p => formData.permissions.includes(p.id)).length;
                    const allSelected = selectedCount === categoryPerms.length;
                    
                    return (
                      <div key={category} className="border border-cyber-border rounded-lg p-4">
                        <label className="flex items-center gap-2 cursor-pointer mb-3">
                          <input
                            type="checkbox"
                            checked={allSelected}
                            onChange={() => handleCategoryToggle(category)}
                            className="w-4 h-4 rounded border-cyber-border bg-cyber-darker text-cyber-accent focus:ring-cyber-accent"
                          />
                          <span className={`px-2 py-0.5 text-xs rounded-full border ${categoryColors[category] || 'bg-gray-500/20 text-gray-400'}`}>
                            {category.toUpperCase()}
                          </span>
                          <span className="text-gray-400 text-sm">
                            ({selectedCount}/{categoryPerms.length})
                          </span>
                        </label>
                        
                        <div className="grid grid-cols-2 gap-2 ml-6">
                          {categoryPerms.map(perm => (
                            <label key={perm.id} className="flex items-center gap-2 cursor-pointer text-sm">
                              <input
                                type="checkbox"
                                checked={formData.permissions.includes(perm.id)}
                                onChange={() => handlePermissionToggle(perm.id)}
                                className="w-3 h-3 rounded border-cyber-border bg-cyber-darker text-cyber-accent focus:ring-cyber-accent"
                              />
                              <span className="text-gray-300">{perm.name}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setShowEditModal(false);
                  setSelectedRole(null);
                  setFormData({ name: '', description: '', permissions: [], is_default: false });
                }}
                className="flex-1 px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-gray-300 hover:border-gray-500"
              >
                Cancel
              </button>
              <button
                onClick={showEditModal ? handleUpdateRole : handleCreateRole}
                disabled={!formData.name}
                className="flex-1 px-4 py-2 bg-cyber-accent text-cyber-dark font-medium rounded-lg hover:bg-cyber-accent-light flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Check className="w-4 h-4" />
                {showEditModal ? 'Save Changes' : 'Create Role'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoleManagement;

