/**
 * Releases Page
 * 
 * Manage release versions and target dates from external sources
 * like Smartsheet or manual entry.
 */

import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Plus,
  Upload,
  RefreshCw,
  Target,
  AlertTriangle,
  CheckCircle,
  Clock,
  Trash2,
  Edit,
  ExternalLink,
  FileSpreadsheet,
  FileText,
  Webhook,
  ChevronRight,
  BarChart3,
  Users,
  GitBranch,
  Shield
} from 'lucide-react';
import axios from 'axios';

interface Release {
  release_id: string;
  version: string;
  name?: string;
  description?: string;
  target_date: string;
  status: string;
  release_type: string;
  source: string;
  project_key?: string;
  epic_key?: string;
  repo_name?: string;
  branch?: string;
  release_manager?: string;
  metrics?: ReleaseMetrics;
  milestones?: Milestone[];
  risks?: Risk[];
  created_at: string;
  updated_at: string;
}

interface ReleaseMetrics {
  total_tickets: number;
  completed_tickets: number;
  ticket_completion_rate: number;
  build_success_rate: number;
  test_coverage: number;
  critical_vulnerabilities: number;
  days_until_release: number;
  readiness_score: number;
  go_no_go: string;
}

interface Milestone {
  id: string;
  name: string;
  target_date: string;
  completed: boolean;
}

interface Risk {
  risk_id: string;
  title: string;
  severity: string;
  status: string;
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

const statusColors: Record<string, string> = {
  planning: 'bg-slate-500',
  in_progress: 'bg-blue-500',
  code_freeze: 'bg-purple-500',
  testing: 'bg-amber-500',
  uat: 'bg-orange-500',
  staging: 'bg-cyan-500',
  ready: 'bg-green-500',
  deployed: 'bg-emerald-600',
  cancelled: 'bg-red-500',
  delayed: 'bg-rose-500'
};

const statusLabels: Record<string, string> = {
  planning: 'Planning',
  in_progress: 'In Progress',
  code_freeze: 'Code Freeze',
  testing: 'Testing',
  uat: 'UAT',
  staging: 'Staging',
  ready: 'Ready',
  deployed: 'Deployed',
  cancelled: 'Cancelled',
  delayed: 'Delayed'
};

export const Releases: React.FC = () => {
  const [releases, setReleases] = useState<Release[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [, setSelectedRelease] = useState<Release | null>(null);
  const [view, setView] = useState<'list' | 'calendar'>('list');
  const [summary, setSummary] = useState({
    total: 0,
    upcoming: 0,
    overdue: 0,
    at_risk: 0
  });

  useEffect(() => {
    fetchReleases();
    fetchCalendarView();
  }, []);

  const fetchReleases = async () => {
    try {
      const response = await axios.get(`${API_URL}/releases`);
      setReleases(response.data.releases || []);
    } catch (error) {
      console.error('Failed to fetch releases:', error);
      // Set mock data for demo
      setReleases(getMockReleases());
    } finally {
      setLoading(false);
    }
  };

  const fetchCalendarView = async () => {
    try {
      const response = await axios.get(`${API_URL}/releases/calendar`);
      setSummary(response.data.summary || summary);
    } catch (error) {
      // Use mock summary
      setSummary({
        total: 5,
        upcoming: 3,
        overdue: 1,
        at_risk: 1
      });
    }
  };

  const getDaysUntilRelease = (targetDate: string): number => {
    const target = new Date(targetDate);
    const now = new Date();
    const diff = target.getTime() - now.getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  };

  const getReadinessColor = (score: number): string => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-amber-400';
    return 'text-red-400';
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleDeleteRelease = async (releaseId: string) => {
    if (!confirm('Are you sure you want to delete this release?')) return;
    
    try {
      await axios.delete(`${API_URL}/releases/${releaseId}`);
      setReleases(releases.filter(r => r.release_id !== releaseId));
    } catch (error) {
      console.error('Failed to delete release:', error);
    }
  };

  const handleRefreshMetrics = async (releaseId: string) => {
    try {
      await axios.get(`${API_URL}/releases/${releaseId}/metrics?refresh=true`);
      fetchReleases();
    } catch (error) {
      console.error('Failed to refresh metrics:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-3">
            <Calendar className="w-7 h-7 text-cyber-accent" />
            Release Management
          </h1>
          <p className="text-gray-400 mt-1">
            Track release versions and target dates from external sources
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setView(view === 'list' ? 'calendar' : 'list')}
            className="px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 flex items-center gap-2"
          >
            {view === 'list' ? <Calendar className="w-4 h-4" /> : <BarChart3 className="w-4 h-4" />}
            {view === 'list' ? 'Calendar View' : 'List View'}
          </button>
          <button
            onClick={() => setShowImportModal(true)}
            className="px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Import
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-cyber-accent text-gray-900 rounded-lg hover:bg-cyber-accent/80 font-medium flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Release
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total Releases</p>
              <p className="text-2xl font-bold text-gray-100">{summary.total}</p>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-lg">
              <Calendar className="w-6 h-6 text-blue-400" />
            </div>
          </div>
        </div>
        
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Upcoming</p>
              <p className="text-2xl font-bold text-green-400">{summary.upcoming}</p>
            </div>
            <div className="p-3 bg-green-500/10 rounded-lg">
              <Target className="w-6 h-6 text-green-400" />
            </div>
          </div>
        </div>
        
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">At Risk</p>
              <p className="text-2xl font-bold text-amber-400">{summary.at_risk}</p>
            </div>
            <div className="p-3 bg-amber-500/10 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-amber-400" />
            </div>
          </div>
        </div>
        
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Overdue</p>
              <p className="text-2xl font-bold text-red-400">{summary.overdue}</p>
            </div>
            <div className="p-3 bg-red-500/10 rounded-lg">
              <Clock className="w-6 h-6 text-red-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Release List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 text-cyber-accent animate-spin" />
        </div>
      ) : releases.length === 0 ? (
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-12 text-center">
          <Calendar className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-300 mb-2">No Releases Yet</h3>
          <p className="text-gray-500 mb-6">
            Create a release manually or import from Smartsheet, CSV, or API
          </p>
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-2 bg-cyber-accent text-gray-900 rounded-lg font-medium flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Release
            </button>
            <button
              onClick={() => setShowImportModal(true)}
              className="px-6 py-2 bg-gray-800 text-gray-300 rounded-lg flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Import Data
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {releases.map((release) => {
            const daysUntil = getDaysUntilRelease(release.target_date);
            const isOverdue = daysUntil < 0 && release.status !== 'deployed';
            const isAtRisk = daysUntil <= 14 && daysUntil >= 0 && release.status !== 'deployed';
            
            return (
              <div
                key={release.release_id}
                className={`bg-gray-900/50 border rounded-xl p-5 transition-all hover:border-gray-700 ${
                  isOverdue ? 'border-red-500/50' : isAtRisk ? 'border-amber-500/50' : 'border-gray-800'
                }`}
              >
                <div className="flex items-start justify-between">
                  {/* Left: Release Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium text-white ${statusColors[release.status] || 'bg-gray-500'}`}>
                        {statusLabels[release.status] || release.status}
                      </span>
                      <span className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400 uppercase">
                        {release.release_type}
                      </span>
                      <span className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-500 flex items-center gap-1">
                        {release.source === 'smartsheet' && <FileSpreadsheet className="w-3 h-3" />}
                        {release.source === 'csv_import' && <FileText className="w-3 h-3" />}
                        {release.source === 'api_webhook' && <Webhook className="w-3 h-3" />}
                        {release.source}
                      </span>
                    </div>
                    
                    <h3 className="text-xl font-semibold text-gray-100 mt-2">
                      {release.version}
                      {release.name && <span className="text-gray-400 font-normal ml-2">"{release.name}"</span>}
                    </h3>
                    
                    {release.description && (
                      <p className="text-gray-400 text-sm mt-1">{release.description}</p>
                    )}
                    
                    <div className="flex items-center gap-6 mt-3 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        Target: {formatDate(release.target_date)}
                      </span>
                      {release.project_key && (
                        <span className="flex items-center gap-1">
                          <ExternalLink className="w-4 h-4" />
                          {release.project_key}
                        </span>
                      )}
                      {release.repo_name && (
                        <span className="flex items-center gap-1">
                          <GitBranch className="w-4 h-4" />
                          {release.repo_name}
                        </span>
                      )}
                      {release.release_manager && (
                        <span className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          {release.release_manager}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Right: Days & Metrics */}
                  <div className="text-right ml-6">
                    <div className={`text-3xl font-bold ${
                      isOverdue ? 'text-red-400' : 
                      isAtRisk ? 'text-amber-400' : 
                      'text-gray-100'
                    }`}>
                      {release.status === 'deployed' ? (
                        <CheckCircle className="w-8 h-8 text-green-400" />
                      ) : (
                        <>
                          {Math.abs(daysUntil)}
                          <span className="text-sm font-normal text-gray-500 ml-1">
                            {isOverdue ? 'days overdue' : 'days left'}
                          </span>
                        </>
                      )}
                    </div>
                    
                    {release.metrics && (
                      <div className="flex items-center gap-4 mt-3 text-sm">
                        <div className="text-center">
                          <div className={`text-lg font-semibold ${getReadinessColor(release.metrics.readiness_score)}`}>
                            {release.metrics.readiness_score.toFixed(0)}%
                          </div>
                          <div className="text-xs text-gray-500">Ready</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-semibold text-gray-300">
                            {release.metrics.ticket_completion_rate.toFixed(0)}%
                          </div>
                          <div className="text-xs text-gray-500">Tickets</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-semibold text-gray-300 flex items-center gap-1">
                            {release.metrics.critical_vulnerabilities > 0 && (
                              <Shield className="w-4 h-4 text-red-400" />
                            )}
                            {release.metrics.critical_vulnerabilities}
                          </div>
                          <div className="text-xs text-gray-500">Critical</div>
                        </div>
                      </div>
                    )}
                    
                    <div className="flex items-center gap-2 mt-3">
                      <button
                        onClick={() => handleRefreshMetrics(release.release_id)}
                        className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg"
                        title="Refresh Metrics"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setSelectedRelease(release)}
                        className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg"
                        title="Edit Release"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteRelease(release.release_id)}
                        className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-800 rounded-lg"
                        title="Delete Release"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <ChevronRight className="w-5 h-5 text-gray-600" />
                    </div>
                  </div>
                </div>
                
                {/* Milestones Progress */}
                {release.milestones && release.milestones.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-800">
                    <div className="flex items-center gap-2 overflow-x-auto pb-2">
                      {release.milestones.map((milestone) => (
                        <div
                          key={milestone.id}
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs whitespace-nowrap ${
                            milestone.completed
                              ? 'bg-green-500/10 text-green-400'
                              : new Date(milestone.target_date) < new Date()
                                ? 'bg-red-500/10 text-red-400'
                                : 'bg-gray-800 text-gray-400'
                          }`}
                        >
                          {milestone.completed ? (
                            <CheckCircle className="w-3 h-3" />
                          ) : (
                            <Clock className="w-3 h-3" />
                          )}
                          {milestone.name}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create Release Modal */}
      {showCreateModal && (
        <CreateReleaseModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            fetchReleases();
          }}
        />
      )}

      {/* Import Modal */}
      {showImportModal && (
        <ImportModal
          onClose={() => setShowImportModal(false)}
          onImported={() => {
            setShowImportModal(false);
            fetchReleases();
          }}
        />
      )}
    </div>
  );
};

// Create Release Modal Component
const CreateReleaseModal: React.FC<{
  onClose: () => void;
  onCreated: () => void;
}> = ({ onClose, onCreated }) => {
  const [formData, setFormData] = useState({
    version: '',
    name: '',
    description: '',
    target_date: '',
    release_type: 'minor',
    project_key: '',
    epic_key: '',
    repo_name: '',
    branch: 'main',
    release_manager: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API_URL}/releases`, formData);
      onCreated();
    } catch (error) {
      console.error('Failed to create release:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-xl font-semibold text-gray-100 flex items-center gap-2">
            <Plus className="w-5 h-5 text-cyber-accent" />
            Create New Release
          </h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Version <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={formData.version}
                onChange={e => setFormData({...formData, version: e.target.value})}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
                placeholder="v2.1.0"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Release Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={e => setFormData({...formData, name: e.target.value})}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
                placeholder="Phoenix"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={e => setFormData({...formData, description: e.target.value})}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
              rows={2}
              placeholder="Brief description of this release..."
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Target Date <span className="text-red-400">*</span>
              </label>
              <input
                type="date"
                value={formData.target_date}
                onChange={e => setFormData({...formData, target_date: e.target.value})}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Release Type</label>
              <select
                value={formData.release_type}
                onChange={e => setFormData({...formData, release_type: e.target.value})}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
              >
                <option value="major">Major</option>
                <option value="minor">Minor</option>
                <option value="patch">Patch</option>
                <option value="hotfix">Hotfix</option>
                <option value="feature">Feature</option>
              </select>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Jira Project Key</label>
              <input
                type="text"
                value={formData.project_key}
                onChange={e => setFormData({...formData, project_key: e.target.value})}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
                placeholder="PROJ"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Epic Key</label>
              <input
                type="text"
                value={formData.epic_key}
                onChange={e => setFormData({...formData, epic_key: e.target.value})}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
                placeholder="PROJ-100"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Repository</label>
              <input
                type="text"
                value={formData.repo_name}
                onChange={e => setFormData({...formData, repo_name: e.target.value})}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
                placeholder="nexus-backend"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Release Manager</label>
              <input
                type="email"
                value={formData.release_manager}
                onChange={e => setFormData({...formData, release_manager: e.target.value})}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
                placeholder="manager@company.com"
              />
            </div>
          </div>
          
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-cyber-accent text-gray-900 rounded-lg font-medium hover:bg-cyber-accent/80 flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Create Release
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Import Modal Component
const ImportModal: React.FC<{
  onClose: () => void;
  onImported: () => void;
}> = ({ onClose, onImported }) => {
  const [importType, setImportType] = useState<'smartsheet' | 'csv' | 'webhook'>('smartsheet');
  const [loading, setLoading] = useState(false);
  const [smartsheetConfig, setSmartsheetConfig] = useState({
    api_token: '',
    sheet_id: ''
  });
  const [csvData, setCsvData] = useState('');

  const handleSmartsheetSync = async () => {
    if (!smartsheetConfig.api_token || !smartsheetConfig.sheet_id) {
      alert('Please provide API token and Sheet ID');
      return;
    }
    
    setLoading(true);
    try {
      await axios.post(`${API_URL}/releases/sync/smartsheet`, smartsheetConfig);
      alert('Smartsheet sync initiated. Releases will be imported shortly.');
      onImported();
    } catch (error) {
      console.error('Smartsheet sync failed:', error);
      alert('Sync failed. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const handleCsvImport = async () => {
    if (!csvData.trim()) {
      alert('Please paste CSV data');
      return;
    }
    
    setLoading(true);
    try {
      await axios.post(`${API_URL}/releases/sync/csv`, csvData, {
        headers: { 'Content-Type': 'text/plain' }
      });
      onImported();
    } catch (error) {
      console.error('CSV import failed:', error);
      alert('Import failed. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-800 rounded-xl max-w-2xl w-full">
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-xl font-semibold text-gray-100 flex items-center gap-2">
            <Upload className="w-5 h-5 text-cyber-accent" />
            Import Releases
          </h2>
        </div>
        
        <div className="p-6">
          {/* Import Type Tabs */}
          <div className="flex border-b border-gray-800 mb-6">
            <button
              onClick={() => setImportType('smartsheet')}
              className={`px-4 py-2 text-sm font-medium flex items-center gap-2 border-b-2 -mb-px ${
                importType === 'smartsheet'
                  ? 'border-cyber-accent text-cyber-accent'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <FileSpreadsheet className="w-4 h-4" />
              Smartsheet
            </button>
            <button
              onClick={() => setImportType('csv')}
              className={`px-4 py-2 text-sm font-medium flex items-center gap-2 border-b-2 -mb-px ${
                importType === 'csv'
                  ? 'border-cyber-accent text-cyber-accent'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <FileText className="w-4 h-4" />
              CSV
            </button>
            <button
              onClick={() => setImportType('webhook')}
              className={`px-4 py-2 text-sm font-medium flex items-center gap-2 border-b-2 -mb-px ${
                importType === 'webhook'
                  ? 'border-cyber-accent text-cyber-accent'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <Webhook className="w-4 h-4" />
              Webhook
            </button>
          </div>
          
          {/* Smartsheet Form */}
          {importType === 'smartsheet' && (
            <div className="space-y-4">
              <p className="text-gray-400 text-sm">
                Connect to Smartsheet to automatically sync release data.
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  API Token
                </label>
                <input
                  type="password"
                  value={smartsheetConfig.api_token}
                  onChange={e => setSmartsheetConfig({...smartsheetConfig, api_token: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
                  placeholder="Your Smartsheet API token"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Sheet ID
                </label>
                <input
                  type="text"
                  value={smartsheetConfig.sheet_id}
                  onChange={e => setSmartsheetConfig({...smartsheetConfig, sheet_id: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none"
                  placeholder="1234567890"
                />
              </div>
              <button
                onClick={handleSmartsheetSync}
                disabled={loading}
                className="w-full px-4 py-2 bg-cyber-accent text-gray-900 rounded-lg font-medium hover:bg-cyber-accent/80 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <FileSpreadsheet className="w-4 h-4" />}
                Sync from Smartsheet
              </button>
            </div>
          )}
          
          {/* CSV Form */}
          {importType === 'csv' && (
            <div className="space-y-4">
              <p className="text-gray-400 text-sm">
                Paste CSV data with columns: version, target_date, name (optional), status (optional)
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  CSV Data
                </label>
                <textarea
                  value={csvData}
                  onChange={e => setCsvData(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:border-cyber-accent focus:outline-none font-mono text-sm"
                  rows={8}
                  placeholder="version,target_date,name,status&#10;v2.1.0,2025-02-15,Phoenix,planning&#10;v2.2.0,2025-03-01,Ember,planning"
                />
              </div>
              <button
                onClick={handleCsvImport}
                disabled={loading}
                className="w-full px-4 py-2 bg-cyber-accent text-gray-900 rounded-lg font-medium hover:bg-cyber-accent/80 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                Import CSV
              </button>
            </div>
          )}
          
          {/* Webhook Info */}
          {importType === 'webhook' && (
            <div className="space-y-4">
              <p className="text-gray-400 text-sm">
                Configure external systems to send release data to this webhook endpoint.
              </p>
              <div className="bg-gray-800 p-4 rounded-lg">
                <p className="text-sm text-gray-400 mb-2">Webhook URL:</p>
                <code className="text-cyber-accent text-sm break-all">
                  {window.location.origin}/api/releases/sync/webhook
                </code>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <p className="text-sm text-gray-400 mb-2">Expected Payload:</p>
                <pre className="text-xs text-gray-300 overflow-x-auto">
{`{
  "action": "create",
  "source": "your-system",
  "release": {
    "version": "v2.1.0",
    "target_date": "2025-02-15T00:00:00Z",
    "name": "Phoenix",
    "status": "planning"
  }
}`}
                </pre>
              </div>
            </div>
          )}
        </div>
        
        <div className="p-6 border-t border-gray-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// Mock data generator
const getMockReleases = (): Release[] => [
  {
    release_id: 'rel-abc123',
    version: 'v2.1.0',
    name: 'Phoenix',
    description: 'Major feature release with new analytics dashboard',
    target_date: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'in_progress',
    release_type: 'minor',
    source: 'manual',
    project_key: 'NEXUS',
    repo_name: 'nexus-backend',
    branch: 'release/2.1',
    release_manager: 'release-manager@company.com',
    metrics: {
      total_tickets: 45,
      completed_tickets: 32,
      ticket_completion_rate: 71,
      build_success_rate: 94,
      test_coverage: 87,
      critical_vulnerabilities: 0,
      days_until_release: 21,
      readiness_score: 78,
      go_no_go: 'PENDING'
    },
    milestones: [
      { id: 'ms-1', name: 'Planning', target_date: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(), completed: true },
      { id: 'ms-2', name: 'Development', target_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), completed: false },
      { id: 'ms-3', name: 'Code Freeze', target_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(), completed: false },
      { id: 'ms-4', name: 'UAT', target_date: new Date(Date.now() + 18 * 24 * 60 * 60 * 1000).toISOString(), completed: false },
      { id: 'ms-5', name: 'Go-Live', target_date: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000).toISOString(), completed: false }
    ],
    risks: [],
    created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    release_id: 'rel-def456',
    version: 'v2.0.5',
    name: 'Hotfix',
    description: 'Security patch for CVE-2025-1234',
    target_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'testing',
    release_type: 'hotfix',
    source: 'smartsheet',
    project_key: 'NEXUS',
    repo_name: 'nexus-backend',
    branch: 'hotfix/2.0.5',
    release_manager: 'security-lead@company.com',
    metrics: {
      total_tickets: 5,
      completed_tickets: 4,
      ticket_completion_rate: 80,
      build_success_rate: 100,
      test_coverage: 92,
      critical_vulnerabilities: 1,
      days_until_release: 3,
      readiness_score: 85,
      go_no_go: 'CONDITIONAL'
    },
    milestones: [
      { id: 'ms-1', name: 'Fix', target_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), completed: true },
      { id: 'ms-2', name: 'Testing', target_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(), completed: false },
      { id: 'ms-3', name: 'Deploy', target_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(), completed: false }
    ],
    risks: [],
    created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    release_id: 'rel-ghi789',
    version: 'v2.0.4',
    name: '',
    description: 'Bug fixes and performance improvements',
    target_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'deployed',
    release_type: 'patch',
    source: 'csv_import',
    project_key: 'NEXUS',
    repo_name: 'nexus-backend',
    branch: 'main',
    metrics: {
      total_tickets: 12,
      completed_tickets: 12,
      ticket_completion_rate: 100,
      build_success_rate: 100,
      test_coverage: 89,
      critical_vulnerabilities: 0,
      days_until_release: 0,
      readiness_score: 100,
      go_no_go: 'GO'
    },
    milestones: [],
    risks: [],
    created_at: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
  }
];

export default Releases;

