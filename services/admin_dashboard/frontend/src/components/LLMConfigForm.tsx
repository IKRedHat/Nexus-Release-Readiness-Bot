import { useState, useEffect } from 'react'
import { 
  Save, 
  Eye, 
  EyeOff, 
  Loader2, 
  RefreshCw,
  Cpu,
  Cloud,
  Server,
  Zap,
  CheckCircle2,
  AlertCircle,
  Info,
  ChevronDown
} from 'lucide-react'
import axios from 'axios'

const API_BASE = '/api'

// =============================================================================
// Type Definitions
// =============================================================================

interface LLMProvider {
  display_name: string
  description: string
  required_fields: string[]
  optional_fields: string[]
  default_model: string
  supports_streaming: boolean
  supports_function_calling: boolean
}

interface LLMConfig {
  provider: string
  model: string
  api_key?: string
  base_url?: string
  temperature: number
  max_tokens: number
  // Provider-specific fields
  azure_endpoint?: string
  azure_api_version?: string
  azure_deployment?: string
  organization?: string
}

interface Toast {
  message: string
  type: 'success' | 'error' | 'info'
}

// =============================================================================
// Provider Icons
// =============================================================================

const providerIcons: Record<string, any> = {
  openai: Cloud,
  azure_openai: Cloud,
  gemini: Zap,
  anthropic: Cpu,
  ollama: Server,
  groq: Zap,
  vllm: Server,
  mock: Cpu
}

const providerColors: Record<string, string> = {
  openai: 'from-emerald-500 to-green-600',
  azure_openai: 'from-blue-500 to-cyan-600',
  gemini: 'from-purple-500 to-pink-600',
  anthropic: 'from-orange-500 to-amber-600',
  ollama: 'from-gray-500 to-slate-600',
  groq: 'from-red-500 to-rose-600',
  vllm: 'from-indigo-500 to-violet-600',
  mock: 'from-gray-600 to-gray-700'
}

// =============================================================================
// Provider Field Configuration
// =============================================================================

interface FieldConfig {
  key: string
  label: string
  type: 'text' | 'password' | 'number' | 'select'
  placeholder?: string
  description?: string
  options?: string[]
  min?: number
  max?: number
  step?: number
}

const providerFieldConfig: Record<string, FieldConfig[]> = {
  openai: [
    { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-...', description: 'Your OpenAI API key' },
    { key: 'organization', label: 'Organization ID', type: 'text', placeholder: 'org-... (optional)', description: 'Optional organization ID' },
    { key: 'base_url', label: 'Base URL', type: 'text', placeholder: 'https://api.openai.com/v1 (optional)', description: 'Custom API endpoint' },
  ],
  azure_openai: [
    { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'Your Azure OpenAI key', description: 'Azure OpenAI API key' },
    { key: 'azure_endpoint', label: 'Endpoint', type: 'text', placeholder: 'https://your-resource.openai.azure.com/', description: 'Your Azure OpenAI endpoint' },
    { key: 'azure_deployment', label: 'Deployment Name', type: 'text', placeholder: 'gpt-4o-deployment', description: 'The deployment name for your model' },
    { key: 'azure_api_version', label: 'API Version', type: 'text', placeholder: '2024-02-15-preview', description: 'Azure OpenAI API version' },
  ],
  gemini: [
    { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'Your Google AI API key', description: 'API key from Google AI Studio' },
  ],
  anthropic: [
    { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-ant-...', description: 'Your Anthropic API key' },
    { key: 'base_url', label: 'Base URL', type: 'text', placeholder: 'https://api.anthropic.com (optional)', description: 'Custom API endpoint' },
  ],
  ollama: [
    { key: 'base_url', label: 'Ollama URL', type: 'text', placeholder: 'http://localhost:11434', description: 'URL of your Ollama server' },
  ],
  groq: [
    { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'gsk_...', description: 'Your Groq API key' },
  ],
  vllm: [
    { key: 'base_url', label: 'vLLM URL', type: 'text', placeholder: 'http://localhost:8000/v1', description: 'URL of your vLLM server' },
    { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'Optional API key', description: 'API key if authentication is enabled' },
  ],
  mock: [],
}

// Model suggestions per provider
const providerModels: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo', 'o1-preview', 'o1-mini'],
  azure_openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-35-turbo'],
  gemini: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-1.5-flash-8b'],
  anthropic: ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
  ollama: ['llama3.1:8b', 'llama3.1:70b', 'mistral:7b', 'codellama:13b', 'mixtral:8x7b', 'qwen2:7b'],
  groq: ['llama-3.1-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
  vllm: ['meta-llama/Llama-3.1-8B-Instruct', 'meta-llama/Llama-3.1-70B-Instruct', 'mistralai/Mistral-7B-Instruct-v0.3'],
  mock: ['mock'],
}

// =============================================================================
// Main Component
// =============================================================================

export default function LLMConfigForm() {
  const [providers, setProviders] = useState<Record<string, LLMProvider>>({})
  const [config, setConfig] = useState<LLMConfig>({
    provider: 'mock',
    model: 'mock',
    temperature: 0.7,
    max_tokens: 4096,
  })
  const [originalConfig, setOriginalConfig] = useState<LLMConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})
  const [toast, setToast] = useState<Toast | null>(null)
  const [hasChanges, setHasChanges] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)

  // Load initial data
  useEffect(() => {
    loadData()
  }, [])

  // Track changes
  useEffect(() => {
    if (originalConfig) {
      const changed = JSON.stringify(config) !== JSON.stringify(originalConfig)
      setHasChanges(changed)
    }
  }, [config, originalConfig])

  const loadData = async () => {
    try {
      setLoading(true)
      const [providersRes, configRes] = await Promise.all([
        axios.get(`${API_BASE}/llm/providers`),
        axios.get(`${API_BASE}/llm/config`)
      ])
      setProviders(providersRes.data.providers)
      setConfig(configRes.data)
      setOriginalConfig(configRes.data)
    } catch (error) {
      console.error('Failed to load LLM config:', error)
      showToast('Failed to load LLM configuration', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setTestResult(null)
    try {
      await axios.post(`${API_BASE}/llm/config`, config)
      setOriginalConfig({ ...config })
      setHasChanges(false)
      showToast('LLM configuration saved successfully', 'success')
    } catch (error: any) {
      console.error('Failed to save config:', error)
      showToast(error.response?.data?.detail || 'Failed to save configuration', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const response = await axios.post(`${API_BASE}/llm/test`, config)
      setTestResult({
        success: response.data.success,
        message: response.data.message
      })
      if (response.data.success) {
        showToast('LLM connection test successful!', 'success')
      } else {
        showToast('LLM connection test failed', 'error')
      }
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.response?.data?.detail || 'Connection test failed'
      })
      showToast('LLM connection test failed', 'error')
    } finally {
      setTesting(false)
    }
  }

  const showToast = (message: string, type: Toast['type']) => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }))
  }

  const togglePasswordVisibility = (key: string) => {
    setShowPasswords(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const handleProviderChange = (newProvider: string) => {
    const providerConfig = providers[newProvider]
    setConfig(prev => ({
      ...prev,
      provider: newProvider,
      model: providerConfig?.default_model || providerModels[newProvider]?.[0] || '',
      // Clear provider-specific fields
      api_key: '',
      base_url: '',
      azure_endpoint: '',
      azure_api_version: '',
      azure_deployment: '',
      organization: '',
    }))
    setTestResult(null)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-cyber-accent mx-auto mb-4" />
          <p className="text-gray-400">Loading LLM configuration...</p>
        </div>
      </div>
    )
  }

  const selectedProvider = providers[config.provider]
  const Icon = providerIcons[config.provider] || Cloud
  const colorClass = providerColors[config.provider] || providerColors.mock

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${colorClass} flex items-center justify-center`}>
              <Icon className="w-6 h-6 text-white" />
            </div>
            LLM Configuration
          </h2>
          <p className="text-gray-400 mt-1">
            Configure your AI/LLM provider for intelligent automation
          </p>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={handleTest}
            disabled={testing || !config.provider || config.provider === 'mock'}
            className={`
              px-4 py-2 rounded-lg flex items-center gap-2 transition-all
              ${config.provider === 'mock' 
                ? 'bg-cyber-border text-gray-500 cursor-not-allowed' 
                : 'bg-blue-600/20 border border-blue-500/50 text-blue-400 hover:bg-blue-600/30'
              }
            `}
          >
            {testing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            Test Connection
          </button>
          
          <button
            onClick={handleSave}
            disabled={saving || !hasChanges}
            className={`
              px-4 py-2 rounded-lg flex items-center gap-2 transition-all
              ${hasChanges 
                ? 'bg-cyber-accent text-cyber-dark hover:bg-cyber-accent/90' 
                : 'bg-cyber-border text-gray-500 cursor-not-allowed'
              }
            `}
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save Configuration
          </button>
        </div>
      </div>

      {/* Test Result Banner */}
      {testResult && (
        <div className={`
          flex items-center gap-3 p-4 rounded-lg border
          ${testResult.success 
            ? 'bg-emerald-900/30 border-emerald-500/50 text-emerald-300' 
            : 'bg-red-900/30 border-red-500/50 text-red-300'
          }
        `}>
          {testResult.success ? (
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
          )}
          <span>{testResult.message}</span>
        </div>
      )}

      {/* Provider Selection */}
      <div className="bg-cyber-card border border-cyber-border rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Cloud className="w-5 h-5 text-cyber-accent" />
          LLM Provider
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(providers).map(([key, provider]) => {
            const ProviderIcon = providerIcons[key] || Cloud
            const isSelected = config.provider === key
            return (
              <button
                key={key}
                onClick={() => handleProviderChange(key)}
                className={`
                  p-4 rounded-lg border-2 transition-all text-left
                  ${isSelected 
                    ? 'border-cyber-accent bg-cyber-accent/10' 
                    : 'border-cyber-border bg-cyber-dark hover:border-gray-600'
                  }
                `}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`
                    w-8 h-8 rounded-lg bg-gradient-to-br ${providerColors[key]} 
                    flex items-center justify-center
                  `}>
                    <ProviderIcon className="w-4 h-4 text-white" />
                  </div>
                  {isSelected && (
                    <CheckCircle2 className="w-4 h-4 text-cyber-accent ml-auto" />
                  )}
                </div>
                <p className="font-medium text-white text-sm">{provider.display_name}</p>
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{provider.description}</p>
              </button>
            )
          })}
        </div>
      </div>

      {/* Model Selection */}
      <div className="bg-cyber-card border border-cyber-border rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-cyber-accent" />
          Model Selection
        </h3>
        
        <div className="grid md:grid-cols-2 gap-6">
          {/* Model */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Model Name</label>
            <div className="relative">
              <select
                value={config.model}
                onChange={(e) => updateConfig('model', e.target.value)}
                className="w-full px-4 py-3 bg-cyber-dark border border-cyber-border rounded-lg text-white focus:border-cyber-accent focus:outline-none transition-colors appearance-none"
              >
                {(providerModels[config.provider] || []).map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
            </div>
            <p className="text-xs text-gray-500">
              Or enter a custom model name below
            </p>
            <input
              type="text"
              value={config.model}
              onChange={(e) => updateConfig('model', e.target.value)}
              placeholder="Custom model name..."
              className="w-full px-4 py-2 bg-cyber-dark border border-cyber-border rounded-lg text-white placeholder-gray-500 focus:border-cyber-accent focus:outline-none transition-colors text-sm"
            />
          </div>

          {/* Temperature & Max Tokens */}
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-300">Temperature</label>
                <span className="text-sm text-cyber-accent font-mono">{config.temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={config.temperature}
                onChange={(e) => updateConfig('temperature', parseFloat(e.target.value))}
                className="w-full h-2 bg-cyber-dark rounded-lg appearance-none cursor-pointer accent-cyber-accent"
              />
              <p className="text-xs text-gray-500">
                Higher values make output more random, lower values more focused
              </p>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">Max Tokens</label>
              <input
                type="number"
                min="1"
                max="128000"
                value={config.max_tokens}
                onChange={(e) => updateConfig('max_tokens', parseInt(e.target.value) || 4096)}
                className="w-full px-4 py-2 bg-cyber-dark border border-cyber-border rounded-lg text-white focus:border-cyber-accent focus:outline-none transition-colors"
              />
              <p className="text-xs text-gray-500">
                Maximum number of tokens in the response
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Provider-Specific Configuration */}
      {config.provider !== 'mock' && providerFieldConfig[config.provider]?.length > 0 && (
        <div className="bg-cyber-card border border-cyber-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Icon className="w-5 h-5 text-cyber-accent" />
            {selectedProvider?.display_name} Configuration
          </h3>
          
          <div className="space-y-6">
            {providerFieldConfig[config.provider].map((field) => (
              <div key={field.key} className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="block text-sm font-medium text-gray-300">
                    {field.label}
                    {providerFieldConfig[config.provider].find(f => f.key === field.key) && (
                      <span className="ml-2 text-xs text-gray-500">
                        {selectedProvider?.required_fields.includes(field.key) ? '(required)' : '(optional)'}
                      </span>
                    )}
                  </label>
                </div>

                {field.type === 'password' ? (
                  <div className="relative">
                    <input
                      type={showPasswords[field.key] ? 'text' : 'password'}
                      value={(config as any)[field.key] || ''}
                      onChange={(e) => updateConfig(field.key, e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full px-4 py-3 pr-12 bg-cyber-dark border border-cyber-border rounded-lg text-white placeholder-gray-500 focus:border-cyber-accent focus:outline-none transition-colors font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => togglePasswordVisibility(field.key)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                    >
                      {showPasswords[field.key] ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                ) : (
                  <input
                    type={field.type}
                    value={(config as any)[field.key] || ''}
                    onChange={(e) => updateConfig(field.key, e.target.value)}
                    placeholder={field.placeholder}
                    className="w-full px-4 py-3 bg-cyber-dark border border-cyber-border rounded-lg text-white placeholder-gray-500 focus:border-cyber-accent focus:outline-none transition-colors"
                  />
                )}

                {field.description && (
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <Info className="w-3 h-3" />
                    {field.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Provider Info Card */}
      {selectedProvider && (
        <div className="bg-cyber-dark border border-cyber-border rounded-lg p-4">
          <div className="flex items-start gap-4">
            <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${colorClass} flex items-center justify-center flex-shrink-0`}>
              <Icon className="w-7 h-7 text-white" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-white">{selectedProvider.display_name}</h4>
              <p className="text-sm text-gray-400 mt-1">{selectedProvider.description}</p>
              <div className="flex flex-wrap gap-2 mt-3">
                {selectedProvider.supports_streaming && (
                  <span className="px-2 py-1 bg-emerald-900/30 text-emerald-400 rounded text-xs">
                    Streaming ✓
                  </span>
                )}
                {selectedProvider.supports_function_calling && (
                  <span className="px-2 py-1 bg-blue-900/30 text-blue-400 rounded text-xs">
                    Function Calling ✓
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`
          fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg z-50
          flex items-center gap-3 animate-slide-up
          ${toast.type === 'success' ? 'bg-emerald-900/90 border border-emerald-500' : 
            toast.type === 'error' ? 'bg-red-900/90 border border-red-500' :
            'bg-blue-900/90 border border-blue-500'}
        `}>
          {toast.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : toast.type === 'error' ? (
            <AlertCircle className="w-5 h-5 text-red-400" />
          ) : (
            <Info className="w-5 h-5 text-blue-400" />
          )}
          <span className={
            toast.type === 'success' ? 'text-emerald-100' : 
            toast.type === 'error' ? 'text-red-100' : 
            'text-blue-100'
          }>
            {toast.message}
          </span>
        </div>
      )}
    </div>
  )
}

