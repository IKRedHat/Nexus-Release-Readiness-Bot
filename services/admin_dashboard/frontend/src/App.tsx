import { Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Settings, 
  Activity, 
  Shield,
  Zap,
  Menu,
  X,
  BarChart3,
  Calendar,
  Users,
  Lightbulb,
  LogOut,
  User,
  ChevronDown
} from 'lucide-react'
import { useState, useEffect, createContext, useContext } from 'react'
import Dashboard from './pages/Dashboard'
import SettingsPage from './pages/Settings'
import HealthPage from './pages/Health'
import MetricsPage from './pages/Metrics'
import ReleasesPage from './pages/Releases'
import LoginPage from './pages/Login'
import UserManagement from './pages/UserManagement'
import RoleManagement from './pages/RoleManagement'
import FeatureRequests from './pages/FeatureRequests'

// Auto-detect API URL based on environment
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  if (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')) {
    return 'https://nexus-admin-api-63b4.onrender.com';
  }
  return 'http://localhost:8088';
};
const API_URL = getApiUrl();

// Auth Context
interface AuthUser {
  id: string;
  email: string;
  name: string;
  roles: string[];
  permissions: string[];
  is_admin: boolean;
  avatar_url?: string;
}

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  logout: () => {},
});

export const useAuth = () => useContext(AuthContext);

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode; requiredPermission?: string }> = ({ 
  children, 
  requiredPermission 
}) => {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  if (requiredPermission && user && !user.is_admin && !user.permissions.includes(requiredPermission)) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Shield className="w-12 h-12 mx-auto text-red-400 mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Access Denied</h2>
          <p className="text-gray-400">You don't have permission to access this page.</p>
        </div>
      </div>
    );
  }
  
  return <>{children}</>;
};

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [user, setUser] = useState<AuthUser | null>(null)
  const location = useLocation()
  
  // Check auth on mount and handle SSO callback
  useEffect(() => {
    // Check for SSO callback
    const params = new URLSearchParams(location.search);
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');
    
    if (accessToken && refreshToken) {
      localStorage.setItem('nexus_access_token', accessToken);
      localStorage.setItem('nexus_refresh_token', refreshToken);
      window.history.replaceState({}, '', location.pathname);
    }
    
    // Load user from storage
    const storedUser = localStorage.getItem('nexus_user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem('nexus_user');
      }
    }
    
    // Fetch current user if token exists
    const token = localStorage.getItem('nexus_access_token');
    if (token && !storedUser) {
      fetchCurrentUser();
    }
  }, [location]);
  
  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('nexus_access_token')}`,
        },
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        localStorage.setItem('nexus_user', JSON.stringify(userData));
      } else {
        // Token invalid
        localStorage.removeItem('nexus_access_token');
        localStorage.removeItem('nexus_refresh_token');
        localStorage.removeItem('nexus_user');
      }
    } catch (err) {
      console.error('Failed to fetch user:', err);
    }
  };
  
  const logout = () => {
    localStorage.removeItem('nexus_access_token');
    localStorage.removeItem('nexus_refresh_token');
    localStorage.removeItem('nexus_user');
    setUser(null);
    window.location.href = '/login';
  };
  
  const isAuthenticated = !!user || !!localStorage.getItem('nexus_access_token');

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/releases', icon: Calendar, label: 'Releases' },
    { to: '/metrics', icon: BarChart3, label: 'Observability' },
    { to: '/health', icon: Activity, label: 'Health Monitor' },
    { to: '/feature-requests', icon: Lightbulb, label: 'Feature Requests' },
    { to: '/settings', icon: Settings, label: 'Configuration' },
  ]
  
  const adminNavItems = [
    { to: '/admin/users', icon: Users, label: 'User Management', permission: 'users:view' },
    { to: '/admin/roles', icon: Shield, label: 'Role Management', permission: 'roles:view' },
  ]
  
  // Show login page without sidebar
  if (location.pathname === '/login') {
    return (
      <AuthContext.Provider value={{ user, isAuthenticated, logout }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </AuthContext.Provider>
    );
  }
  
  // For SSO callback
  if (location.pathname === '/auth/callback') {
    return (
      <div className="min-h-screen bg-cyber-darker flex items-center justify-center">
        <div className="text-center">
          <Zap className="w-12 h-12 mx-auto text-cyber-accent animate-pulse mb-4" />
          <p className="text-white">Completing authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, logout }}>
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
          <nav className="p-4 space-y-2 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 180px)' }}>
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
            
            {/* Admin Section */}
            {user?.is_admin && (
              <>
                <div className="pt-4 mt-4 border-t border-cyber-border">
                  <p className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Administration
                  </p>
                </div>
                {adminNavItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setSidebarOpen(false)}
                    className={({ isActive }) => `
                      flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200
                      ${isActive 
                        ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30' 
                        : 'text-gray-400 hover:text-white hover:bg-cyber-card'
                      }
                    `}
                  >
                    <item.icon size={20} />
                    <span className="font-medium">{item.label}</span>
                  </NavLink>
                ))}
              </>
            )}
          </nav>

          {/* User Profile & Footer */}
          <div className="absolute bottom-0 left-0 right-0 border-t border-cyber-border">
            {/* User Profile */}
            {user && (
              <div className="p-3 border-b border-cyber-border">
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-cyber-card transition-colors"
                  >
                    <div className="w-8 h-8 bg-cyber-accent/20 rounded-full flex items-center justify-center">
                      {user.avatar_url ? (
                        <img src={user.avatar_url} alt={user.name} className="w-8 h-8 rounded-full" />
                      ) : (
                        <User className="w-4 h-4 text-cyber-accent" />
                      )}
                    </div>
                    <div className="flex-1 text-left">
                      <div className="text-sm font-medium text-white truncate">{user.name}</div>
                      <div className="text-xs text-gray-500 truncate">{user.email}</div>
                    </div>
                    <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
                  </button>
                  
                  {userMenuOpen && (
                    <div className="absolute bottom-full left-0 right-0 mb-2 bg-cyber-darker border border-cyber-border rounded-lg shadow-xl overflow-hidden">
                      <div className="p-3 border-b border-cyber-border">
                        <div className="text-sm text-gray-400">Signed in as</div>
                        <div className="text-white font-medium truncate">{user.email}</div>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {user.roles.map(role => (
                            <span key={role} className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded-full">
                              {role}
                            </span>
                          ))}
                        </div>
                      </div>
                      <button
                        onClick={logout}
                        className="w-full flex items-center gap-2 px-4 py-3 text-red-400 hover:bg-cyber-card transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Version */}
            <div className="p-4">
              <div className="flex items-center space-x-2 text-xs text-gray-500">
                <Shield size={14} />
                <span>Version 2.4.0</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="lg:ml-64 min-h-screen">
          <div className="p-6 lg:p-8">
            <Routes>
              <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/releases" element={<ProtectedRoute><ReleasesPage /></ProtectedRoute>} />
              <Route path="/metrics" element={<ProtectedRoute><MetricsPage /></ProtectedRoute>} />
              <Route path="/health" element={<ProtectedRoute><HealthPage /></ProtectedRoute>} />
              <Route path="/feature-requests" element={<ProtectedRoute><FeatureRequests /></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
              <Route path="/admin/users" element={<ProtectedRoute requiredPermission="users:view"><UserManagement /></ProtectedRoute>} />
              <Route path="/admin/roles" element={<ProtectedRoute requiredPermission="roles:view"><RoleManagement /></ProtectedRoute>} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
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
    </AuthContext.Provider>
  )
}

export default App

