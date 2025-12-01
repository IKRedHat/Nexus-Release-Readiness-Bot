import { useState, useEffect } from 'react'
import { 
  Power, 
  Activity, 
  Database, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  AlertCircle,
  RefreshCw,
  Zap,
  Server
} from 'lucide-react'
import axios from 'axios'
import ModeSwitch from '../components/ModeSwitch'
import StatusCard from '../components/StatusCard'

const API_BASE = '/api'

interface SystemHealth {
  status: string
  mode: string
  agents: AgentHealth[]
  healthy_count: number
  total_count: number
  timestamp: string
}

interface AgentHealth {
  agent_id: string
  name: string
  url: string
  status: string
  response_time_ms: number | null
  details: any
  last_checked: string
}

interface DashboardStats {
  mode: string
  config_count: number
  healthy_agents: number
  total_agents: number
  redis_connected: boolean
  uptime_seconds: number
}

export default function Dashboard() {
  const [mode, setMode] = useState<string>('mock')
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = async () => {
    try {
      const [modeRes, healthRes, statsRes] = await Promise.all([
        axios.get(`${API_BASE}/mode`),
        axios.get(`${API_BASE}/health-check`),
        axios.get(`${API_BASE}/stats`)
      ])
      setMode(modeRes.data.mode)
      setHealth(healthRes.data)
      setStats(statsRes.data)
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchData()
    setRefreshing(false)
  }

  const handleModeChange = async (newMode: string) => {
    try {
      await axios.post(`${API_BASE}/mode`, { mode: newMode })
      setMode(newMode)
      await fetchData()
    } catch (error) {
      console.error('Failed to change mode:', error)
    }
  }

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-cyber-accent mx-auto mb-4" />
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
            <Zap className="w-8 h-8 text-cyber-accent" />
            System Dashboard
          </h1>
          <p className="text-gray-400 mt-1">Monitor and control your Nexus instance</p>
        </div>
        
        <div className="flex items-center gap-4">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 rounded-lg bg-cyber-card border border-cyber-border text-gray-400 hover:text-white hover:border-cyber-accent transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          <ModeSwitch currentMode={mode} onModeChange={handleModeChange} />
        </div>
      </div>

      {/* Mode Alert */}
      {mode === 'live' && (
        <div className="bg-emerald-900/30 border border-emerald-500/50 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-emerald-400" />
          <div>
            <p className="text-emerald-400 font-medium">Live Mode Active</p>
            <p className="text-emerald-300/70 text-sm">All agents are connecting to production services</p>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="System Mode"
          value={mode.toUpperCase()}
          icon={Power}
          status={mode === 'live' ? 'success' : 'warning'}
          subtitle={mode === 'live' ? 'Production' : 'Development'}
        />
        <StatusCard
          title="Agent Health"
          value={`${health?.healthy_count || 0}/${health?.total_count || 0}`}
          icon={Activity}
          status={
            health?.healthy_count === health?.total_count 
              ? 'success' 
              : health?.healthy_count === 0 
                ? 'error' 
                : 'warning'
          }
          subtitle={health?.status || 'Unknown'}
        />
        <StatusCard
          title="Redis Connection"
          value={stats?.redis_connected ? 'Connected' : 'Disconnected'}
          icon={Database}
          status={stats?.redis_connected ? 'success' : 'error'}
          subtitle="Config Store"
        />
        <StatusCard
          title="Uptime"
          value={stats ? formatUptime(stats.uptime_seconds) : '0h 0m'}
          icon={Clock}
          status="neutral"
          subtitle="Since last restart"
        />
      </div>

      {/* Agent Health Grid */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Server className="w-5 h-5 text-cyber-accent" />
          Agent Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {health?.agents.map((agent) => (
            <div 
              key={agent.agent_id}
              className="bg-cyber-card border border-cyber-border rounded-lg p-4 card-hover"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-white">{agent.name}</h3>
                  <p className="text-xs text-gray-500 font-mono mt-1">{agent.url}</p>
                </div>
                <div className={`
                  w-3 h-3 rounded-full status-pulse
                  ${agent.status === 'healthy' ? 'bg-cyber-success' : 'bg-cyber-danger'}
                `} />
              </div>
              
              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {agent.status === 'healthy' ? (
                    <CheckCircle2 className="w-4 h-4 text-cyber-success" />
                  ) : (
                    <XCircle className="w-4 h-4 text-cyber-danger" />
                  )}
                  <span className={`text-sm ${
                    agent.status === 'healthy' ? 'text-cyber-success' : 'text-cyber-danger'
                  }`}>
                    {agent.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
                  </span>
                </div>
                {agent.response_time_ms && (
                  <span className="text-xs text-gray-500">
                    {agent.response_time_ms.toFixed(0)}ms
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Overview */}
        <div className="bg-cyber-card border border-cyber-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">System Overview</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Configuration Keys</span>
              <span className="text-white font-mono">{stats?.config_count || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Agents</span>
              <span className="text-white font-mono">{stats?.total_agents || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Healthy Agents</span>
              <span className="text-cyber-success font-mono">{stats?.healthy_agents || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Last Health Check</span>
              <span className="text-white text-sm">
                {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-cyber-card border border-cyber-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button 
              onClick={handleRefresh}
              className="w-full py-2 px-4 bg-cyber-border hover:bg-gray-700 rounded-lg text-white transition-colors flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh Health Status
            </button>
            <button 
              onClick={() => handleModeChange(mode === 'mock' ? 'live' : 'mock')}
              className={`w-full py-2 px-4 rounded-lg text-white transition-colors flex items-center justify-center gap-2 ${
                mode === 'mock' 
                  ? 'bg-emerald-600 hover:bg-emerald-700' 
                  : 'bg-amber-600 hover:bg-amber-700'
              }`}
            >
              <Power className="w-4 h-4" />
              Switch to {mode === 'mock' ? 'Live' : 'Mock'} Mode
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

