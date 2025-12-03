/**
 * Login Page - SSO Authentication
 * 
 * Provides authentication via:
 * - Local login (development)
 * - SSO providers (Okta, Azure AD, Google, GitHub)
 */

import React, { useState, useEffect } from 'react';
import {
  Shield, Lock, Mail, Eye, EyeOff,
  LogIn, Loader2, AlertCircle, CheckCircle,
  Github, Chrome
} from 'lucide-react';

// Custom icons for SSO providers
const OktaIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0C5.389 0 0 5.389 0 12s5.389 12 12 12 12-5.389 12-12S18.611 0 12 0zm0 18c-3.314 0-6-2.686-6-6s2.686-6 6-6 6 2.686 6 6-2.686 6-6 6z"/>
  </svg>
);

const AzureIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M5.483 21.3H24L14.025 4.013l-3.038 8.347 5.836 6.938L5.483 21.3zM13.23 2.7L6.105 8.677 0 19.253h5.505l7.725-16.553z"/>
  </svg>
);

interface AuthProvider {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
}

const providers: Record<string, AuthProvider> = {
  okta: { id: 'okta', name: 'Okta', icon: <OktaIcon />, color: 'bg-blue-600 hover:bg-blue-700' },
  azure_ad: { id: 'azure_ad', name: 'Microsoft', icon: <AzureIcon />, color: 'bg-blue-500 hover:bg-blue-600' },
  google: { id: 'google', name: 'Google', icon: <Chrome className="w-5 h-5" />, color: 'bg-red-500 hover:bg-red-600' },
  github: { id: 'github', name: 'GitHub', icon: <Github className="w-5 h-5" />, color: 'bg-gray-700 hover:bg-gray-800' },
};

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8088';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [availableProviders, setAvailableProviders] = useState<string[]>(['local']);
  
  useEffect(() => {
    // Fetch available auth providers
    fetch(`${API_URL}/auth/providers`)
      .then(res => res.json())
      .then(data => {
        setAvailableProviders(data.providers || ['local']);
      })
      .catch(() => {
        setAvailableProviders(['local']);
      });
  }, []);
  
  const handleLocalLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Login failed');
      }
      
      const data = await response.json();
      
      // Store tokens
      localStorage.setItem('nexus_access_token', data.access_token);
      localStorage.setItem('nexus_refresh_token', data.refresh_token);
      localStorage.setItem('nexus_user', JSON.stringify(data.user));
      
      setSuccess('Login successful! Redirecting...');
      
      // Redirect to dashboard
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
      
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSSOLogin = async (providerId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/auth/sso/${providerId}`);
      const data = await response.json();
      
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        throw new Error('Failed to get authorization URL');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'SSO login failed');
      setLoading(false);
    }
  };
  
  const ssoProviders = availableProviders.filter(p => p !== 'local' && providers[p]);
  
  return (
    <div className="min-h-screen bg-cyber-darker flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyber-accent/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
      </div>
      
      <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-cyber-dark rounded-2xl border border-cyber-border">
            <Shield className="w-12 h-12 text-cyber-accent" />
          </div>
        </div>
        
        <h2 className="text-center text-3xl font-bold text-white mb-2">
          Welcome to Nexus
        </h2>
        <p className="text-center text-gray-400 mb-8">
          Sign in to access the Admin Dashboard
        </p>
        
        {/* Login Card */}
        <div className="bg-cyber-dark border border-cyber-border rounded-xl shadow-xl p-8">
          {/* Error/Success Messages */}
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3 text-red-400">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          
          {success && (
            <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg flex items-center gap-3 text-green-400">
              <CheckCircle className="w-5 h-5 flex-shrink-0" />
              <span>{success}</span>
            </div>
          )}
          
          {/* SSO Providers */}
          {ssoProviders.length > 0 && (
            <>
              <div className="space-y-3 mb-6">
                {ssoProviders.map(providerId => {
                  const provider = providers[providerId];
                  return (
                    <button
                      key={providerId}
                      onClick={() => handleSSOLogin(providerId)}
                      disabled={loading}
                      className={`w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg text-white font-medium transition-colors ${provider.color} disabled:opacity-50`}
                    >
                      {provider.icon}
                      Continue with {provider.name}
                    </button>
                  );
                })}
              </div>
              
              <div className="relative mb-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-cyber-border" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-cyber-dark text-gray-400">or continue with email</span>
                </div>
              </div>
            </>
          )}
          
          {/* Local Login Form */}
          <form onSubmit={handleLocalLogin} className="space-y-5">
            {/* Email Field */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  required
                  className="w-full pl-11 pr-4 py-3 bg-cyber-darker border border-cyber-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyber-accent focus:border-transparent"
                />
              </div>
            </div>
            
            {/* Password Field */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-11 pr-12 py-3 bg-cyber-darker border border-cyber-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyber-accent focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
            
            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-cyber-accent text-cyber-dark font-semibold rounded-lg hover:bg-cyber-accent-light transition-colors disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  <LogIn className="w-5 h-5" />
                  Sign In
                </>
              )}
            </button>
          </form>
          
          {/* Help Text */}
          <p className="mt-6 text-center text-sm text-gray-400">
            Need access? Contact your system administrator.
          </p>
        </div>
        
        {/* Footer */}
        <p className="mt-8 text-center text-xs text-gray-500">
          Nexus Release Automation System v2.4.0
        </p>
      </div>
    </div>
  );
};

export default LoginPage;

