import { Power, Zap, FlaskConical } from 'lucide-react'

interface ModeSwitchProps {
  currentMode: string
  onModeChange: (mode: string) => void
  disabled?: boolean
}

export default function ModeSwitch({ currentMode, onModeChange, disabled }: ModeSwitchProps) {
  const isLive = currentMode === 'live'

  return (
    <div className="flex items-center gap-3">
      <span className={`text-sm font-medium ${!isLive ? 'text-cyber-warning' : 'text-gray-500'}`}>
        Mock
      </span>
      
      <button
        onClick={() => onModeChange(isLive ? 'mock' : 'live')}
        disabled={disabled}
        className={`
          relative w-20 h-10 rounded-full transition-all duration-300 ease-in-out
          ${isLive 
            ? 'bg-gradient-to-r from-emerald-600 to-emerald-500 glow-green' 
            : 'bg-gradient-to-r from-amber-600 to-amber-500 glow-yellow'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:scale-105'}
          focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-cyber-dark
          ${isLive ? 'focus:ring-emerald-500' : 'focus:ring-amber-500'}
        `}
        title={`Switch to ${isLive ? 'Mock' : 'Live'} mode`}
      >
        {/* Track background pattern */}
        <div className="absolute inset-0 rounded-full overflow-hidden">
          <div className="absolute inset-0 opacity-20">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="absolute h-full w-px bg-white"
                style={{ left: `${(i + 1) * 12.5}%` }}
              />
            ))}
          </div>
        </div>

        {/* Toggle knob */}
        <div
          className={`
            absolute top-1 w-8 h-8 rounded-full bg-white shadow-lg
            flex items-center justify-center
            transition-all duration-300 ease-in-out
            ${isLive ? 'left-10' : 'left-1'}
          `}
        >
          {isLive ? (
            <Zap className="w-4 h-4 text-emerald-600" />
          ) : (
            <FlaskConical className="w-4 h-4 text-amber-600" />
          )}
        </div>

        {/* Status indicator */}
        <div
          className={`
            absolute -top-1 -right-1 w-4 h-4 rounded-full
            flex items-center justify-center
            ${isLive ? 'bg-emerald-400' : 'bg-amber-400'}
            animate-pulse
          `}
        >
          <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-emerald-600' : 'bg-amber-600'}`} />
        </div>
      </button>

      <span className={`text-sm font-medium ${isLive ? 'text-cyber-success' : 'text-gray-500'}`}>
        Live
      </span>
    </div>
  )
}

