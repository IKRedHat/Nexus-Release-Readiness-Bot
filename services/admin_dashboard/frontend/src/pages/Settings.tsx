import { useState, useEffect } from 'react'
import { 
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Settings,
  Database,
  Github,
  Cloud,
  MessageSquare,
  FileText,
  Cpu
} from 'lucide-react'
import axios from 'axios'
import ConfigForm from '../components/ConfigForm'

const API_BASE = '/api'

interface ConfigTemplate {
  name: string
  description: string
  fields: ConfigField[]
}

interface ConfigField {
  key: string
  label: string
  type: string
  placeholder?: string
  options?: string[]
}

interface ConfigValue {
  key: string
  value: string | null
  masked_value: string
  is_sensitive: boolean
  source: string
  env_var: string
  category: string
}

const categoryIcons: Record<string, any> = {
  jira: Database,
  github: Github,
  jenkins: Cpu,
  llm: Cloud,
  slack: MessageSquare,
  confluence: FileText,
  system: Settings,
  agents: Settings,
  other: Settings
}

export default function SettingsPage() {
  const [templates, setTemplates] = useState<Record<string, ConfigTemplate>>({})
  const [config, setConfig] = useState<ConfigValue[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [activeCategory, setActiveCategory] = useState<string>('jira')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [templatesRes, configRes] = await Promise.all([
        axios.get(`${API_BASE}/config/templates`),
        axios.get(`${API_BASE}/config`)
      ])
      setTemplates(templatesRes.data)
      setConfig(configRes.data.config)
    } catch (error) {
      console.error('Failed to fetch config:', error)
      showToast('Failed to load configuration', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (key: string, value: string) => {
    setSaving(key)
    try {
      await axios.post(`${API_BASE}/config`, { key, value })
      showToast('Configuration saved successfully', 'success')
      await fetchData()
    } catch (error) {
      console.error('Failed to save config:', error)
      showToast('Failed to save configuration', 'error')
    } finally {
      setSaving(null)
    }
  }

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  const getConfigValue = (key: string): string => {
    const item = config.find(c => c.key === key)
    return item?.value || ''
  }

  const getMaskedValue = (key: string): string => {
    const item = config.find(c => c.key === key)
    return item?.masked_value || ''
  }

  const isSensitive = (key: string): boolean => {
    const item = config.find(c => c.key === key)
    return item?.is_sensitive || false
  }

  const categories = Object.keys(templates)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-cyber-accent mx-auto mb-4" />
          <p className="text-gray-400">Loading configuration...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-3">
          <Settings className="w-8 h-8 text-cyber-accent" />
          System Configuration
        </h1>
        <p className="text-gray-400 mt-1">Manage API keys, URLs, and integration settings</p>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-cyber-border pb-4">
        {categories.map((category) => {
          const Icon = categoryIcons[category] || Settings
          return (
            <button
              key={category}
              onClick={() => setActiveCategory(category)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg transition-all
                ${activeCategory === category
                  ? 'bg-cyber-accent/10 text-cyber-accent border border-cyber-accent/30'
                  : 'bg-cyber-card text-gray-400 hover:text-white border border-cyber-border'
                }
              `}
            >
              <Icon className="w-4 h-4" />
              <span className="capitalize">{category}</span>
            </button>
          )
        })}
      </div>

      {/* Active Category Form */}
      {templates[activeCategory] && (
        <div className="bg-cyber-card border border-cyber-border rounded-lg p-6">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-white">{templates[activeCategory].name}</h2>
            <p className="text-gray-400 text-sm mt-1">{templates[activeCategory].description}</p>
          </div>

          <div className="space-y-6">
            {templates[activeCategory].fields.map((field) => (
              <ConfigForm
                key={field.key}
                field={field}
                value={getConfigValue(field.key)}
                maskedValue={getMaskedValue(field.key)}
                isSensitive={isSensitive(field.key)}
                onSave={(value) => handleSave(field.key, value)}
                saving={saving === field.key}
              />
            ))}
          </div>
        </div>
      )}

      {/* All Configuration Table */}
      <div className="bg-cyber-card border border-cyber-border rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-cyber-border">
          <h2 className="text-lg font-semibold text-white">All Configuration Values</h2>
          <p className="text-gray-400 text-sm">View all configuration keys and their sources</p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-cyber-dark">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Key</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Value</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Source</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Category</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyber-border">
              {config.map((item) => (
                <tr key={item.key} className="hover:bg-cyber-dark/50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-mono text-sm text-cyber-accent">{item.key}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-mono text-sm text-gray-300">
                      {item.masked_value || <span className="text-gray-500 italic">Not set</span>}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`
                      px-2 py-1 rounded text-xs font-medium
                      ${item.source === 'redis' ? 'bg-emerald-900/50 text-emerald-400' :
                        item.source === 'env' ? 'bg-blue-900/50 text-blue-400' :
                        'bg-gray-800 text-gray-400'}
                    `}>
                      {item.source}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-400 capitalize">{item.category}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div className={`
          fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg toast-enter
          flex items-center gap-3
          ${toast.type === 'success' ? 'bg-emerald-900/90 border border-emerald-500' : 'bg-red-900/90 border border-red-500'}
        `}>
          {toast.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-400" />
          )}
          <span className={toast.type === 'success' ? 'text-emerald-100' : 'text-red-100'}>
            {toast.message}
          </span>
        </div>
      )}
    </div>
  )
}

