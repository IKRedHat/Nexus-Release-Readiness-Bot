import { useState } from 'react'
import { Save, Eye, EyeOff, Loader2 } from 'lucide-react'

interface ConfigField {
  key: string
  label: string
  type: string
  placeholder?: string
  options?: string[]
}

interface ConfigFormProps {
  field: ConfigField
  value: string
  maskedValue: string
  isSensitive: boolean
  onSave: (value: string) => void
  saving: boolean
}

export default function ConfigForm({ 
  field, 
  value, 
  maskedValue, 
  isSensitive, 
  onSave, 
  saving 
}: ConfigFormProps) {
  const [inputValue, setInputValue] = useState(value)
  const [showPassword, setShowPassword] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)

  const handleChange = (newValue: string) => {
    setInputValue(newValue)
    setHasChanges(newValue !== value)
  }

  const handleSave = () => {
    onSave(inputValue)
    setHasChanges(false)
  }

  const renderInput = () => {
    if (field.type === 'select' && field.options) {
      return (
        <select
          value={inputValue}
          onChange={(e) => handleChange(e.target.value)}
          className="w-full px-4 py-3 bg-cyber-dark border border-cyber-border rounded-lg text-white focus:border-cyber-accent focus:outline-none transition-colors"
        >
          <option value="">Select {field.label}</option>
          {field.options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      )
    }

    if (field.type === 'password') {
      return (
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            value={inputValue}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={maskedValue || field.placeholder}
            className="w-full px-4 py-3 pr-12 bg-cyber-dark border border-cyber-border rounded-lg text-white placeholder-gray-500 focus:border-cyber-accent focus:outline-none transition-colors font-mono"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
      )
    }

    return (
      <input
        type={field.type}
        value={inputValue}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={field.placeholder}
        className="w-full px-4 py-3 bg-cyber-dark border border-cyber-border rounded-lg text-white placeholder-gray-500 focus:border-cyber-accent focus:outline-none transition-colors"
      />
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-300">
          {field.label}
          {isSensitive && (
            <span className="ml-2 px-2 py-0.5 text-xs bg-amber-900/50 text-amber-400 rounded">
              Sensitive
            </span>
          )}
        </label>
        <span className="text-xs text-gray-500 font-mono">{field.key}</span>
      </div>

      <div className="flex gap-3">
        <div className="flex-1">
          {renderInput()}
        </div>

        <button
          onClick={handleSave}
          disabled={!hasChanges || saving}
          className={`
            px-4 py-3 rounded-lg flex items-center gap-2 transition-all
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
          Save
        </button>
      </div>

      {/* Current value indicator */}
      {maskedValue && !hasChanges && (
        <p className="text-xs text-gray-500">
          Current: <span className="font-mono">{maskedValue}</span>
        </p>
      )}
    </div>
  )
}

