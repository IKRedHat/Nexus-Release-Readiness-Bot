import { Routes, Route, NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Settings, 
  Activity, 
  Shield,
  Zap,
  Menu,
  X
} from 'lucide-react'
import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import SettingsPage from './pages/Settings'
import HealthPage from './pages/Health'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/health', icon: Activity, label: 'Health Monitor' },
    { to: '/settings', icon: Settings, label: 'Configuration' },
  ]

  return (
    <div className="min-h-screen bg-cyber-darker bg-grid">
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-lg bg-cyber-card border border-cyber-border text-gray-400 hover:text-white"
        >
          {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-cyber-dark border-r border-cyber-border
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}>
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-cyber-border">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyber-accent to-emerald-600 flex items-center justify-center">
              <Zap className="w-6 h-6 text-cyber-dark" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Nexus</h1>
              <p className="text-xs text-gray-500">Admin Dashboard</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => `
                flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200
                ${isActive 
                  ? 'bg-cyber-accent/10 text-cyber-accent border border-cyber-accent/30' 
                  : 'text-gray-400 hover:text-white hover:bg-cyber-card'
                }
              `}
            >
              <item.icon size={20} />
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-cyber-border">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <Shield size={14} />
            <span>Version 2.3.0</span>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="lg:ml-64 min-h-screen">
        <div className="p-6 lg:p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/health" element={<HealthPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}

export default App

