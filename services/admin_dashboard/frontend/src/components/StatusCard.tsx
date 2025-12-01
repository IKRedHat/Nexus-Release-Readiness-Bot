import { LucideIcon } from 'lucide-react'

interface StatusCardProps {
  title: string
  value: string
  icon: LucideIcon
  status: 'success' | 'warning' | 'error' | 'neutral'
  subtitle?: string
}

export default function StatusCard({ title, value, icon: Icon, status, subtitle }: StatusCardProps) {
  const statusStyles = {
    success: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      icon: 'text-emerald-400',
      value: 'text-emerald-400',
      glow: 'glow-green'
    },
    warning: {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30',
      icon: 'text-amber-400',
      value: 'text-amber-400',
      glow: 'glow-yellow'
    },
    error: {
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      icon: 'text-red-400',
      value: 'text-red-400',
      glow: 'glow-red'
    },
    neutral: {
      bg: 'bg-cyber-card',
      border: 'border-cyber-border',
      icon: 'text-gray-400',
      value: 'text-white',
      glow: ''
    }
  }

  const style = statusStyles[status]

  return (
    <div className={`
      ${style.bg} ${style.border} border rounded-lg p-5
      transition-all duration-300 card-hover ${style.glow}
    `}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400 mb-1">{title}</p>
          <p className={`text-2xl font-bold ${style.value}`}>{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`
          w-12 h-12 rounded-lg flex items-center justify-center
          ${style.bg} ${style.border} border
        `}>
          <Icon className={`w-6 h-6 ${style.icon}`} />
        </div>
      </div>
    </div>
  )
}

