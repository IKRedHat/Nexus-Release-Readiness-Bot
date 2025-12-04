import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import {
  Activity,
  Cpu,
  Zap,
  AlertTriangle,
  TrendingUp,
  Clock,
  DollarSign,
  CheckCircle,
  XCircle,
  RefreshCw,
  ExternalLink,
  BarChart3,
  PieChartIcon
} from 'lucide-react'
import axios from 'axios'

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
const API_BASE = getApiUrl();

interface MetricCard {
  title: string
  value: string | number
  change?: string
  changeType?: 'positive' | 'negative' | 'neutral'
  icon: React.ReactNode
  color: string
}

interface TimeSeriesData {
  time: string
  requests: number
  errors: number
  latency: number
}

interface AgentMetrics {
  name: string
  requests: number
  errors: number
  avgLatency: number
  status: 'healthy' | 'degraded' | 'unhealthy'
}

interface LLMUsage {
  model: string
  tokens: number
  cost: number
  requests: number
}

const COLORS = ['#00ff88', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function MetricsPage() {
  const [timeRange, setTimeRange] = useState('1h')
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState<{
    summary: MetricCard[]
    timeSeries: TimeSeriesData[]
    agents: AgentMetrics[]
    llmUsage: LLMUsage[]
    hygieneScore: number
    releaseDecisions: { go: number; nogo: number }
  } | null>(null)
  const grafanaUrl = 'http://localhost:3000'

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [timeRange])

  const fetchMetrics = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_BASE}/metrics?range=${timeRange}`)
      setMetrics(response.data)
    } catch (error) {
      // Use mock data if API fails
      setMetrics(getMockMetrics())
    }
    setLoading(false)
  }

  const getMockMetrics = () => ({
    summary: [
      { title: 'Total Requests', value: '12,847', change: '+12%', changeType: 'positive' as const, icon: <Activity size={20} />, color: 'cyber-accent' },
      { title: 'Avg Latency', value: '145ms', change: '-8%', changeType: 'positive' as const, icon: <Clock size={20} />, color: 'blue-500' },
      { title: 'Error Rate', value: '0.3%', change: '+0.1%', changeType: 'negative' as const, icon: <AlertTriangle size={20} />, color: 'amber-500' },
      { title: 'LLM Cost', value: '$4.27', change: '+$0.50', changeType: 'neutral' as const, icon: <DollarSign size={20} />, color: 'purple-500' },
    ],
    timeSeries: generateTimeSeriesData(),
    agents: [
      { name: 'Orchestrator', requests: 3420, errors: 12, avgLatency: 234, status: 'healthy' as const },
      { name: 'Jira Agent', requests: 2180, errors: 5, avgLatency: 156, status: 'healthy' as const },
      { name: 'Git/CI Agent', requests: 1890, errors: 8, avgLatency: 189, status: 'healthy' as const },
      { name: 'Slack Agent', requests: 2456, errors: 3, avgLatency: 98, status: 'healthy' as const },
      { name: 'Hygiene Agent', requests: 890, errors: 2, avgLatency: 312, status: 'healthy' as const },
      { name: 'RCA Agent', requests: 156, errors: 1, avgLatency: 2340, status: 'healthy' as const },
      { name: 'Analytics', requests: 1234, errors: 0, avgLatency: 87, status: 'healthy' as const },
      { name: 'Webhooks', requests: 621, errors: 4, avgLatency: 45, status: 'degraded' as const },
    ],
    llmUsage: [
      { model: 'gemini-1.5-pro', tokens: 145000, cost: 2.18, requests: 234 },
      { model: 'gemini-2.0-flash', tokens: 89000, cost: 1.34, requests: 567 },
      { model: 'gpt-4o', tokens: 23000, cost: 0.69, requests: 45 },
      { model: 'mock', tokens: 12000, cost: 0, requests: 890 },
    ],
    hygieneScore: 87,
    releaseDecisions: { go: 12, nogo: 3 }
  })

  const generateTimeSeriesData = (): TimeSeriesData[] => {
    const data: TimeSeriesData[] = []
    const now = new Date()
    for (let i = 59; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60000)
      data.push({
        time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        requests: Math.floor(Math.random() * 100) + 50,
        errors: Math.floor(Math.random() * 5),
        latency: Math.floor(Math.random() * 100) + 100
      })
    }
    return data
  }

  if (!metrics) return null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="text-cyber-accent" />
            Observability Dashboard
          </h1>
          <p className="text-gray-400 mt-1">Real-time metrics and system performance</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Time Range Selector */}
          <div className="flex bg-cyber-card rounded-lg border border-cyber-border p-1">
            {['1h', '6h', '24h', '7d'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  timeRange === range
                    ? 'bg-cyber-accent text-cyber-dark'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="p-2 rounded-lg bg-cyber-card border border-cyber-border text-gray-400 hover:text-cyber-accent hover:border-cyber-accent/50 transition-all"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          </button>
          <a
            href={grafanaUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-cyber-card border border-cyber-border text-gray-400 hover:text-white hover:border-cyber-accent/50 transition-all"
          >
            <ExternalLink size={16} />
            <span className="text-sm">Grafana</span>
          </a>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.summary.map((card, index) => (
          <div
            key={index}
            className="bg-cyber-card rounded-xl border border-cyber-border p-5 hover:border-cyber-accent/30 transition-all"
          >
            <div className="flex items-start justify-between">
              <div className={`p-2 rounded-lg bg-${card.color}/10 text-${card.color}`}>
                {card.icon}
              </div>
              {card.change && (
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                  card.changeType === 'positive' ? 'bg-green-500/10 text-green-400' :
                  card.changeType === 'negative' ? 'bg-red-500/10 text-red-400' :
                  'bg-gray-500/10 text-gray-400'
                }`}>
                  {card.change}
                </span>
              )}
            </div>
            <div className="mt-4">
              <p className="text-sm text-gray-400">{card.title}</p>
              <p className="text-2xl font-bold text-white mt-1">{card.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Request Traffic */}
        <div className="bg-cyber-card rounded-xl border border-cyber-border p-5">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-cyber-accent" />
            Request Traffic
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics.timeSeries}>
                <defs>
                  <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#00ff88" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="time" stroke="#6b7280" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Area type="monotone" dataKey="requests" stroke="#00ff88" fillOpacity={1} fill="url(#colorRequests)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Latency Distribution */}
        <div className="bg-cyber-card rounded-xl border border-cyber-border p-5">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Clock size={18} className="text-blue-500" />
            Latency Over Time
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics.timeSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="time" stroke="#6b7280" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} unit="ms" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Line type="monotone" dataKey="latency" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Agent Performance & LLM Usage */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Performance Table */}
        <div className="lg:col-span-2 bg-cyber-card rounded-xl border border-cyber-border p-5">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Cpu size={18} className="text-purple-500" />
            Agent Performance
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs text-gray-500 uppercase tracking-wider">
                  <th className="pb-3">Agent</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3">Requests</th>
                  <th className="pb-3">Errors</th>
                  <th className="pb-3">Avg Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cyber-border">
                {metrics.agents.map((agent, index) => (
                  <tr key={index} className="text-sm">
                    <td className="py-3 text-white font-medium">{agent.name}</td>
                    <td className="py-3">
                      <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${
                        agent.status === 'healthy' ? 'bg-green-500/10 text-green-400' :
                        agent.status === 'degraded' ? 'bg-amber-500/10 text-amber-400' :
                        'bg-red-500/10 text-red-400'
                      }`}>
                        {agent.status === 'healthy' ? <CheckCircle size={12} /> : 
                         agent.status === 'degraded' ? <AlertTriangle size={12} /> : 
                         <XCircle size={12} />}
                        {agent.status}
                      </span>
                    </td>
                    <td className="py-3 text-gray-300">{agent.requests.toLocaleString()}</td>
                    <td className="py-3">
                      <span className={agent.errors > 0 ? 'text-red-400' : 'text-gray-400'}>
                        {agent.errors}
                      </span>
                    </td>
                    <td className="py-3 text-gray-300">{agent.avgLatency}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* LLM Usage Pie Chart */}
        <div className="bg-cyber-card rounded-xl border border-cyber-border p-5">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Zap size={18} className="text-amber-500" />
            LLM Token Usage
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.llmUsage}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  fill="#8884d8"
                  paddingAngle={2}
                  dataKey="tokens"
                  nameKey="model"
                >
                  {metrics.llmUsage.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
                  formatter={(value: number) => [value.toLocaleString() + ' tokens', '']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-2">
            {metrics.llmUsage.map((item, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                  <span className="text-gray-400">{item.model}</span>
                </div>
                <span className="text-white font-medium">${item.cost.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row - Hygiene & Decisions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Hygiene Score */}
        <div className="bg-cyber-card rounded-xl border border-cyber-border p-5">
          <h3 className="text-lg font-semibold text-white mb-4">Hygiene Score</h3>
          <div className="flex items-center justify-center">
            <div className="relative w-32 h-32">
              <svg className="w-32 h-32 transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="#1f2937"
                  strokeWidth="12"
                  fill="none"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke={metrics.hygieneScore >= 80 ? '#00ff88' : metrics.hygieneScore >= 60 ? '#f59e0b' : '#ef4444'}
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray={`${(metrics.hygieneScore / 100) * 352} 352`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-3xl font-bold text-white">{metrics.hygieneScore}%</span>
              </div>
            </div>
          </div>
          <p className="text-center text-gray-400 mt-4 text-sm">
            {metrics.hygieneScore >= 80 ? 'Excellent data quality' :
             metrics.hygieneScore >= 60 ? 'Needs improvement' : 'Critical issues'}
          </p>
        </div>

        {/* Release Decisions */}
        <div className="bg-cyber-card rounded-xl border border-cyber-border p-5">
          <h3 className="text-lg font-semibold text-white mb-4">Release Decisions</h3>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { name: 'Go', value: metrics.releaseDecisions.go, fill: '#00ff88' },
                { name: 'No-Go', value: metrics.releaseDecisions.nogo, fill: '#ef4444' }
              ]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="name" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {[
                    { name: 'Go', value: metrics.releaseDecisions.go, fill: '#00ff88' },
                    { name: 'No-Go', value: metrics.releaseDecisions.nogo, fill: '#ef4444' }
                  ].map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-cyber-card rounded-xl border border-cyber-border p-5">
          <h3 className="text-lg font-semibold text-white mb-4">External Dashboards</h3>
          <div className="space-y-3">
            <a
              href={grafanaUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 rounded-lg bg-cyber-darker border border-cyber-border hover:border-cyber-accent/50 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center">
                  <BarChart3 size={16} className="text-orange-500" />
                </div>
                <div>
                  <p className="text-white font-medium">Grafana</p>
                  <p className="text-xs text-gray-500">Full dashboard</p>
                </div>
              </div>
              <ExternalLink size={16} className="text-gray-500 group-hover:text-cyber-accent" />
            </a>
            <a
              href="http://localhost:9090"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 rounded-lg bg-cyber-darker border border-cyber-border hover:border-cyber-accent/50 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center">
                  <Activity size={16} className="text-red-500" />
                </div>
                <div>
                  <p className="text-white font-medium">Prometheus</p>
                  <p className="text-xs text-gray-500">Raw metrics</p>
                </div>
              </div>
              <ExternalLink size={16} className="text-gray-500 group-hover:text-cyber-accent" />
            </a>
            <a
              href="http://localhost:16686"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 rounded-lg bg-cyber-darker border border-cyber-border hover:border-cyber-accent/50 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <Zap size={16} className="text-blue-500" />
                </div>
                <div>
                  <p className="text-white font-medium">Jaeger</p>
                  <p className="text-xs text-gray-500">Distributed tracing</p>
                </div>
              </div>
              <ExternalLink size={16} className="text-gray-500 group-hover:text-cyber-accent" />
            </a>
          </div>
        </div>
      </div>

      {/* Embedded Grafana (Optional) */}
      <div className="bg-cyber-card rounded-xl border border-cyber-border p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <PieChartIcon size={18} className="text-orange-500" />
            Grafana Dashboard
          </h3>
          <a
            href={`${grafanaUrl}/d/nexus-overview`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-cyber-accent hover:text-cyber-accent/80 flex items-center gap-1"
          >
            Open in Grafana <ExternalLink size={14} />
          </a>
        </div>
        <div className="bg-cyber-darker rounded-lg border border-cyber-border overflow-hidden">
          <iframe
            src={`${grafanaUrl}/d-solo/nexus-overview/nexus-overview?orgId=1&panelId=1&theme=dark`}
            width="100%"
            height="300"
            frameBorder="0"
            className="w-full"
            title="Grafana Dashboard"
            onError={(e) => {
              const target = e.target as HTMLIFrameElement
              target.style.display = 'none'
              const parent = target.parentElement
              if (parent) {
                parent.innerHTML = `
                  <div class="flex flex-col items-center justify-center h-64 text-gray-500">
                    <svg class="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M12 12h.01M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p>Grafana not available</p>
                    <p class="text-sm mt-1">Start Grafana to see embedded dashboards</p>
                  </div>
                `
              }
            }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-2">
          💡 Configure Grafana to allow embedding: Set <code className="text-cyber-accent">allow_embedding = true</code> in grafana.ini
        </p>
      </div>
    </div>
  )
}

