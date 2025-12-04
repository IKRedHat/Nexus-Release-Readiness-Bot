'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { api, endpoints } from '@/lib/api';
import type { User, LoginResponse } from '@/types';
import { getLocalStorage, setLocalStorage, removeLocalStorage } from '@/lib/utils';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    initAuth();
  }, []);

  const initAuth = async () => {
    const storedUser = getLocalStorage<User | null>('nexus_user', null);
    const token = getLocalStorage<string | null>('nexus_access_token', null);
    
    if (storedUser && token) {
      setUser(storedUser);
      // Optionally refresh user data from API
      try {
        const currentUser = await api.get<User>(endpoints.me);
        setUser(currentUser);
        setLocalStorage('nexus_user', currentUser);
      } catch {
        // Token might be expired, keep stored user for now
      }
    }
    
    setIsLoading(false);
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post<LoginResponse>(endpoints.login, {
        email,
        password,
      });

      setLocalStorage('nexus_access_token', response.access_token);
      setLocalStorage('nexus_refresh_token', response.refresh_token);
      setLocalStorage('nexus_user', response.user);
      
      setUser(response.user);
      router.push('/');
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    removeLocalStorage('nexus_access_token');
    removeLocalStorage('nexus_refresh_token');
    removeLocalStorage('nexus_user');
    setUser(null);
    router.push('/login');
  };

  const refreshUser = async () => {
    try {
      const currentUser = await api.get<User>(endpoints.me);
      setUser(currentUser);
      setLocalStorage('nexus_user', currentUser);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    if (user.is_admin) return true;
    return user.permissions.includes(permission) || user.permissions.includes('*');
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      isAuthenticated: !!user, 
      isLoading, 
      login, 
      logout, 
      refreshUser,
      hasPermission 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

