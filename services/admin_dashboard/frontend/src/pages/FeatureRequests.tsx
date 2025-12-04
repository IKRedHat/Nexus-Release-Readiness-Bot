/**
 * Feature Requests Page
 * 
 * Submit feature requests and bug reports that automatically
 * create Jira tickets with proper field mapping.
 */

import React, { useState, useEffect } from 'react';
import {
  Lightbulb, Bug, PlusCircle, Search, Filter,
  Check, X, ExternalLink, AlertCircle, Loader2,
  ChevronDown, Tag, User, Calendar,
  FileText, Zap, BookOpen, HelpCircle, RefreshCw
} from 'lucide-react';

interface FeatureRequest {
  id: string;
  type: string;
  title: string;
  description: string;
  priority: string;
  status: string;
  component?: string;
  labels: string[];
  submitter_name: string;
  submitter_email: string;
  jira_key?: string;
  jira_url?: string;
  created_at: string;
}

interface RequestOptions {
  types: string[];
  priorities: string[];
  components: string[];
  labels: string[];
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

const typeIcons: Record<string, React.ReactNode> = {
  feature_request: <Lightbulb className="w-5 h-5" />,
  bug_report: <Bug className="w-5 h-5" />,
  improvement: <Zap className="w-5 h-5" />,
  documentation: <BookOpen className="w-5 h-5" />,
  question: <HelpCircle className="w-5 h-5" />,
};

const typeColors: Record<string, string> = {
  feature_request: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  bug_report: 'bg-red-500/20 text-red-400 border-red-500/30',
  improvement: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  documentation: 'bg-green-500/20 text-green-400 border-green-500/30',
  question: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
};

const priorityColors: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-green-500/20 text-green-400 border-green-500/30',
};

const statusColors: Record<string, string> = {
  submitted: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  triaged: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  in_progress: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  completed: 'bg-green-500/20 text-green-400 border-green-500/30',
  rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
  duplicate: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

export const FeatureRequests: React.FC = () => {
  const [requests, setRequests] = useState<FeatureRequest[]>([]);
  const [options, setOptions] = useState<RequestOptions>({
    types: [], priorities: [], components: [], labels: [],
  });
  const [stats, setStats] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    type: 'feature_request',
    title: '',
    description: '',
    priority: 'medium',
    component: '',
    labels: [] as string[],
    // Bug-specific fields
    steps_to_reproduce: '',
    expected_behavior: '',
    actual_behavior: '',
    environment: '',
    browser: '',
    // Feature-specific fields
    use_case: '',
    business_value: '',
    acceptance_criteria: '',
  });
  
  useEffect(() => {
    fetchRequests();
    fetchOptions();
    fetchStats();
  }, []);
  
  const fetchRequests = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/feature-requests`, {
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) throw new Error('Failed to fetch requests');
      
      const data = await response.json();
      setRequests(data.requests || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load requests');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchOptions = async () => {
    try {
      const response = await fetch(`${API_URL}/feature-requests/options`);
      const data = await response.json();
      setOptions(data);
    } catch (err) {
      console.error('Failed to fetch options:', err);
    }
  };
  
  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/feature-requests/stats`, {
        headers: getAuthHeaders(),
      });
      const data = await response.json();
      setStats(data.stats || {});
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };
  
  const handleSubmit = async () => {
    if (!formData.title || !formData.description) {
      setError('Title and description are required');
      return;
    }
    
    if (formData.description.length < 20) {
      setError('Description must be at least 20 characters');
      return;
    }
    
    setSubmitting(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/feature-requests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to submit request');
      }
      
      const data = await response.json();
      
      setShowCreateModal(false);
      setFormData({
        type: 'feature_request', title: '', description: '', priority: 'medium',
        component: '', labels: [], steps_to_reproduce: '', expected_behavior: '',
        actual_behavior: '', environment: '', browser: '', use_case: '',
        business_value: '', acceptance_criteria: '',
      });
      
      if (data.jira_created) {
        setSuccess(`Request submitted and Jira ticket ${data.request.jira_key} created!`);
      } else {
        setSuccess('Request submitted successfully!');
      }
      
      fetchRequests();
      fetchStats();
      
      setTimeout(() => setSuccess(null), 5000);
      
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to submit request');
    } finally {
      setSubmitting(false);
    }
  };
  
  const handleLabelToggle = (label: string) => {
    setFormData(prev => ({
      ...prev,
      labels: prev.labels.includes(label)
        ? prev.labels.filter(l => l !== label)
        : [...prev.labels, label],
    }));
  };
  
  const filteredRequests = requests.filter(req => {
    const matchesSearch = 
      req.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      req.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = !typeFilter || req.type === typeFilter;
    return matchesSearch && matchesType;
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
            <Lightbulb className="w-7 h-7 text-cyber-accent" />
            Feature Requests
          </h1>
          <p className="text-gray-400 mt-1">Submit feature requests and bug reports</p>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={fetchRequests}
            className="p-2 bg-cyber-dark border border-cyber-border rounded-lg hover:border-cyber-accent transition-colors"
          >
            <RefreshCw className="w-5 h-5 text-gray-400" />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-cyber-accent text-cyber-dark font-medium rounded-lg hover:bg-cyber-accent-light transition-colors"
          >
            <PlusCircle className="w-5 h-5" />
            New Request
          </button>
        </div>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Requests', value: Number(stats.total) || 0, color: 'text-cyber-accent' },
          { label: 'Pending', value: Number((stats.by_status as Record<string, number>)?.submitted) || 0, color: 'text-blue-400' },
          { label: 'In Progress', value: Number((stats.by_status as Record<string, number>)?.in_progress) || 0, color: 'text-yellow-400' },
          { label: 'Completed', value: Number((stats.by_status as Record<string, number>)?.completed) || 0, color: 'text-green-400' },
        ].map((stat) => (
          <div key={stat.label} className="bg-cyber-dark border border-cyber-border rounded-xl p-4">
            <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
            <div className="text-gray-400 text-sm">{stat.label}</div>
          </div>
        ))}
      </div>
      
      {/* Messages */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      
      {success && (
        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg flex items-center gap-3 text-green-400">
          <Check className="w-5 h-5" />
          <span>{success}</span>
          <button onClick={() => setSuccess(null)} className="ml-auto">
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
            placeholder="Search requests..."
            className="w-full pl-10 pr-4 py-2 bg-cyber-dark border border-cyber-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyber-accent"
          />
        </div>
        
        <div className="relative">
          <button
            onClick={() => setTypeFilter(typeFilter ? null : 'feature_request')}
            className="flex items-center gap-2 px-4 py-2 bg-cyber-dark border border-cyber-border rounded-lg text-gray-300 hover:border-cyber-accent"
          >
            <Filter className="w-5 h-5" />
            {typeFilter?.replace('_', ' ') || 'All Types'}
            <ChevronDown className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Requests List */}
      <div className="space-y-4">
        {filteredRequests.map(req => (
          <div
            key={req.id}
            className="bg-cyber-dark border border-cyber-border rounded-xl p-5 hover:border-cyber-accent/50 transition-colors"
          >
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-lg ${typeColors[req.type]}`}>
                {typeIcons[req.type]}
              </div>
              
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-white">{req.title}</h3>
                  <span className={`px-2 py-0.5 text-xs rounded-full border ${priorityColors[req.priority]}`}>
                    {req.priority}
                  </span>
                  <span className={`px-2 py-0.5 text-xs rounded-full border ${statusColors[req.status]}`}>
                    {req.status.replace('_', ' ')}
                  </span>
                </div>
                
                <p className="text-gray-400 text-sm line-clamp-2 mb-3">{req.description}</p>
                
                <div className="flex items-center gap-6 text-sm text-gray-500">
                  <div className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    {req.submitter_name}
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {new Date(req.created_at).toLocaleDateString()}
                  </div>
                  {req.component && (
                    <div className="flex items-center gap-1">
                      <FileText className="w-4 h-4" />
                      {req.component}
                    </div>
                  )}
                  {req.jira_key && (
                    <a
                      href={req.jira_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-cyber-accent hover:underline"
                    >
                      <ExternalLink className="w-4 h-4" />
                      {req.jira_key}
                    </a>
                  )}
                </div>
                
                {req.labels.length > 0 && (
                  <div className="flex gap-2 mt-3">
                    {req.labels.map(label => (
                      <span
                        key={label}
                        className="px-2 py-0.5 text-xs bg-cyber-darker text-gray-400 rounded-full"
                      >
                        <Tag className="w-3 h-3 inline mr-1" />
                        {label}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {filteredRequests.length === 0 && (
          <div className="text-center py-12 text-gray-400 bg-cyber-dark border border-cyber-border rounded-xl">
            <Lightbulb className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No requests found</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 text-cyber-accent hover:underline"
            >
              Submit your first request
            </button>
          </div>
        )}
      </div>
      
      {/* Create Request Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto py-8">
          <div className="bg-cyber-dark border border-cyber-border rounded-xl p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <PlusCircle className="w-6 h-6 text-cyber-accent" />
              Submit New Request
            </h2>
            
            <div className="space-y-4">
              {/* Type Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Request Type</label>
                <div className="flex flex-wrap gap-2">
                  {options.types.map(type => (
                    <button
                      key={type}
                      onClick={() => setFormData({ ...formData, type })}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                        formData.type === type
                          ? typeColors[type]
                          : 'border-cyber-border text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      {typeIcons[type]}
                      {type.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Title *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={e => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                  placeholder="Brief, descriptive title"
                  maxLength={200}
                />
                <div className="text-xs text-gray-500 mt-1">{formData.title.length}/200</div>
              </div>
              
              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Description *</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({ ...formData, description: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent resize-none"
                  placeholder="Detailed description of your request..."
                  minLength={20}
                  maxLength={5000}
                />
                <div className="text-xs text-gray-500 mt-1">{formData.description.length}/5000 (min 20)</div>
              </div>
              
              {/* Priority & Component */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Priority</label>
                  <select
                    value={formData.priority}
                    onChange={e => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                  >
                    {options.priorities.map(p => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Component</label>
                  <select
                    value={formData.component}
                    onChange={e => setFormData({ ...formData, component: e.target.value })}
                    className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                  >
                    <option value="">Select component...</option>
                    {options.components.map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              {/* Bug-specific fields */}
              {formData.type === 'bug_report' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Steps to Reproduce</label>
                    <textarea
                      value={formData.steps_to_reproduce}
                      onChange={e => setFormData({ ...formData, steps_to_reproduce: e.target.value })}
                      rows={3}
                      className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent resize-none"
                      placeholder="1. Go to...&#10;2. Click on...&#10;3. See error"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Expected Behavior</label>
                      <textarea
                        value={formData.expected_behavior}
                        onChange={e => setFormData({ ...formData, expected_behavior: e.target.value })}
                        rows={2}
                        className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent resize-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Actual Behavior</label>
                      <textarea
                        value={formData.actual_behavior}
                        onChange={e => setFormData({ ...formData, actual_behavior: e.target.value })}
                        rows={2}
                        className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent resize-none"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Environment</label>
                      <input
                        type="text"
                        value={formData.environment}
                        onChange={e => setFormData({ ...formData, environment: e.target.value })}
                        className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                        placeholder="Production, Staging, Local"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Browser</label>
                      <input
                        type="text"
                        value={formData.browser}
                        onChange={e => setFormData({ ...formData, browser: e.target.value })}
                        className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent"
                        placeholder="Chrome 120, Firefox 121"
                      />
                    </div>
                  </div>
                </>
              )}
              
              {/* Feature-specific fields */}
              {(formData.type === 'feature_request' || formData.type === 'improvement') && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Use Case</label>
                    <textarea
                      value={formData.use_case}
                      onChange={e => setFormData({ ...formData, use_case: e.target.value })}
                      rows={2}
                      className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent resize-none"
                      placeholder="As a [user type], I want to [action] so that [benefit]..."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Business Value</label>
                    <textarea
                      value={formData.business_value}
                      onChange={e => setFormData({ ...formData, business_value: e.target.value })}
                      rows={2}
                      className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent resize-none"
                      placeholder="How will this benefit the team/organization?"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Acceptance Criteria</label>
                    <textarea
                      value={formData.acceptance_criteria}
                      onChange={e => setFormData({ ...formData, acceptance_criteria: e.target.value })}
                      rows={3}
                      className="w-full px-4 py-2 bg-cyber-darker border border-cyber-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyber-accent resize-none"
                      placeholder="- Given [condition], when [action], then [result]"
                    />
                  </div>
                </>
              )}
              
              {/* Labels */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Labels</label>
                <div className="flex flex-wrap gap-2">
                  {options.labels.map(label => (
                    <button
                      key={label}
                      onClick={() => handleLabelToggle(label)}
                      className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                        formData.labels.includes(label)
                          ? 'bg-cyber-accent/20 text-cyber-accent border-cyber-accent/50'
                          : 'border-cyber-border text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Info Box */}
            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-300">
                  <p className="font-medium mb-1">Automatic Jira Integration</p>
                  <p className="text-blue-300/80">
                    Your request will automatically create a Jira ticket with the provided information.
                    You'll receive the Jira ticket key once submitted.
                  </p>
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
                onClick={handleSubmit}
                disabled={submitting || !formData.title || formData.description.length < 20}
                className="flex-1 px-4 py-2 bg-cyber-accent text-cyber-dark font-medium rounded-lg hover:bg-cyber-accent-light flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Submit Request
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeatureRequests;

