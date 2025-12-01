import { useState, useEffect } from 'react'
import { 
  Activity, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  Clock,
  Wifi,
  WifiOff,
  Server,
  AlertTriangle
} from 'lucide-react'
import axios from 'axios'

const API_BASE = '/api'

interface AgentHealth {
  agent_id: string
  name: string
  url: string
  status: string
  response_time_ms: number | null
  details: any
  last_checked: string
}

interface SystemHealth {
  status: string
  mode: string
  agents: AgentHealth[]
  healthy_count: number
  total_count: number
  timestamp: string
}

export default function HealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState<AgentHealth | null>(null)

  const fetchHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE}/health-check`)
      setHealth(response.data)
    } catch (error) {
      console.error('Failed to fetch health:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
    
    if (autoRefresh) {
      const interval = setInterval(fetchHealth, 10000) // Refresh every 10s
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const handleManualRefresh = async () => {
    setRefreshing(true)
    await fetchHealth()
    setRefreshing(false)
  }

  const checkSingleAgent = async (agentId: string) => {
    try {
      const response = await axios.get(`${API_BASE}/health-check/${agentId}`)
      setSelectedAgent(response.data)
    } catch (error) {
      console.error('Failed to check agent:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-cyber-success'
      case 'degraded':
        return 'text-cyber-warning'
      case 'unhealthy':
        return 'text-cyber-danger'
      default:
        return 'text-gray-400'
    }
  }

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-cyber-success/10 border-cyber-success/30'
      case 'degraded':
        return 'bg-cyber-warning/10 border-cyber-warning/30'
      case 'unhealthy':
        return 'bg-cyber-danger/10 border-cyber-danger/30'
      default:
        return 'bg-gray-500/10 border-gray-500/30'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-cyber-accent mx-auto mb-4" />
          <p className="text-gray-400">Checking agent health...</p>
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
            <Activity className="w-8 h-8 text-cyber-accent" />
            Health Monitor
          </h1>
          <p className="text-gray-400 mt-1">Real-time status of all Nexus agents</p>
        </div>

        <div className="flex items-center gap-4">
          {/* Auto-refresh toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="sr-only"
            />
            <div className={`
              w-10 h-6 rounded-full transition-colors relative
              ${autoRefresh ? 'bg-cyber-accent' : 'bg-cyber-border'}
            `}>
              <div className={`
                absolute top-1 w-4 h-4 rounded-full bg-white transition-transform
                ${autoRefresh ? 'left-5' : 'left-1'}
              `} />
            </div>
            <span className="text-sm text-gray-400">Auto-refresh</span>
          </label>

          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-cyber-card border border-cyber-border rounded-lg text-gray-300 hover:text-white hover:border-cyber-accent transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh Now
          </button>
        </div>
      </div>

      {/* Overall Status Banner */}
      {health && (
        <div className={`
          rounded-lg border p-6 ${getStatusBg(health.status)}
        `}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {health.status === 'healthy' ? (
                <CheckCircle2 className="w-10 h-10 text-cyber-success" />
              ) : health.status === 'degraded' ? (
                <AlertTriangle className="w-10 h-10 text-cyber-warning" />
              ) : (
                <XCircle className="w-10 h-10 text-cyber-danger" />
              )}
              <div>
                <h2 className={`text-2xl font-bold ${getStatusColor(health.status)}`}>
                  System {health.status.charAt(0).toUpperCase() + health.status.slice(1)}
                </h2>
                <p className="text-gray-400">
                  {health.healthy_count} of {health.total_count} agents operational
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400">Mode</p>
              <p className={`text-lg font-semibold ${
                health.mode === 'live' ? 'text-cyber-success' : 'text-cyber-warning'
              }`}>
                {health.mode.toUpperCase()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {health?.agents.map((agent) => (
          <div
            key={agent.agent_id}
            onClick={() => checkSingleAgent(agent.agent_id)}
            className={`
              bg-cyber-card border rounded-lg p-5 cursor-pointer transition-all card-hover
              ${agent.status === 'healthy' ? 'border-cyber-border hover:border-cyber-success/50' : 'border-cyber-danger/50'}
            `}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`
                  w-10 h-10 rounded-lg flex items-center justify-center
                  ${agent.status === 'healthy' ? 'bg-cyber-success/20' : 'bg-cyber-danger/20'}
                `}>
                  <Server className={`w-5 h-5 ${
                    agent.status === 'healthy' ? 'text-cyber-success' : 'text-cyber-danger'
                  }`} />
                </div>
                <div>
                  <h3 className="font-semibold text-white">{agent.name}</h3>
                  <p className="text-xs text-gray-500 font-mono">{agent.agent_id}</p>
                </div>
              </div>
              <div className={`
                w-3 h-3 rounded-full status-pulse
                ${agent.status === 'healthy' ? 'bg-cyber-success' : 'bg-cyber-danger'}
              `} />
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                {agent.status === 'healthy' ? (
                  <Wifi className="w-4 h-4 text-cyber-success" />
                ) : (
                  <WifiOff className="w-4 h-4 text-cyber-danger" />
                )}
                <span className={getStatusColor(agent.status)}>
                  {agent.status === 'healthy' ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Clock className="w-4 h-4" />
                {agent.response_time_ms ? (
                  <span>{agent.response_time_ms.toFixed(0)}ms response</span>
                ) : (
                  <span>No response</span>
                )}
              </div>

              <p className="text-xs text-gray-500 font-mono truncate">
                {agent.url}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Agent Details Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-cyber-card border border-cyber-border rounded-lg max-w-lg w-full max-h-[80vh] overflow-auto">
            <div className="p-6 border-b border-cyber-border">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-white">{selectedAgent.name}</h3>
                <button
                  onClick={() => setSelectedAgent(null)}
                  className="text-gray-400 hover:text-white"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm text-gray-400">Status</p>
                <p className={`font-semibold ${getStatusColor(selectedAgent.status)}`}>
                  {selectedAgent.status.charAt(0).toUpperCase() + selectedAgent.status.slice(1)}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-400">URL</p>
                <p className="font-mono text-sm text-gray-300">{selectedAgent.url}</p>
              </div>

              <div>
                <p className="text-sm text-gray-400">Response Time</p>
                <p className="text-white">
                  {selectedAgent.response_time_ms 
                    ? `${selectedAgent.response_time_ms.toFixed(2)}ms`
                    : 'N/A'
                  }
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-400">Last Checked</p>
                <p className="text-white">
                  {new Date(selectedAgent.last_checked).toLocaleString()}
                </p>
              </div>

              {selectedAgent.details && Object.keys(selectedAgent.details).length > 0 && (
                <div>
                  <p className="text-sm text-gray-400 mb-2">Details</p>
                  <pre className="bg-cyber-dark p-3 rounded-lg text-xs text-gray-300 overflow-auto">
                    {JSON.stringify(selectedAgent.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Last Update */}
      {health && (
        <div className="text-center text-sm text-gray-500">
          Last updated: {new Date(health.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  )
}

