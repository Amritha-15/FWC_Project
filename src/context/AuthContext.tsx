import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../utils/api';
import { generateToken } from '../utils/crypto';

export interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'hr' | 'employee' | 'manager' | 'candidate';
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string, selectedRole: string) => Promise<User>;
  register: (name: string, email: string, password: string) => Promise<User>;
  logout: () => void;
  updateUser: (updatedUser: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Seeds mapping for local employee and manager authentication
const SEEDED_USERS: Record<string, { id: number; name: string; role: 'employee' | 'manager' }> = {
  'taylor3@example.com': { id: 3, name: 'Taylor 3', role: 'manager' },
  'morgan4@example.com': { id: 4, name: 'Morgan 4', role: 'manager' },
  'casey5@example.com': { id: 5, name: 'Casey 5', role: 'manager' },
  'riley6@example.com': { id: 6, name: 'Riley 6', role: 'employee' },
  'jamie7@example.com': { id: 7, name: 'Jamie 7', role: 'employee' },
  'avery8@example.com': { id: 8, name: 'Avery 8', role: 'employee' },
  'drew9@example.com': { id: 9, name: 'Drew 9', role: 'employee' },
  'quinn10@example.com': { id: 10, name: 'Quinn 10', role: 'employee' },
  'sam11@example.com': { id: 11, name: 'Sam 11', role: 'employee' },
  'cameron12@example.com': { id: 12, name: 'Cameron 12', role: 'employee' },
  'reese13@example.com': { id: 13, name: 'Reese 13', role: 'employee' },
  'charlie14@example.com': { id: 14, name: 'Charlie 14', role: 'employee' },
  'parker15@example.com': { id: 15, name: 'Parker 15', role: 'employee' },
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Restore session from localStorage on startup
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string, selectedRole: string): Promise<User> => {
    // 1. If Candidate, route to candidate login endpoint
    if (selectedRole === 'candidate') {
      const response = await api.post('/api/candidate/login', { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
      return userData;
    }

    // 2. For Admin, HR, Employee, Manager, route to admin auth/login endpoint
    const response = await api.post('/api/auth/login', { email, password });
    const { access_token, user: userData } = response.data;
    
    if (userData.role !== selectedRole) {
      throw new Error(`Invalid credentials or role selection (expected ${selectedRole}, got ${userData.role})`);
    }

    localStorage.setItem('token', access_token);
    localStorage.setItem('user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (name: string, email: string, password: string): Promise<User> => {
    // Only candidates can self-register
    const response = await api.post('/api/candidate/register', { name, email, password });
    
    // Candidate register returns the user directly. We will automatically log them in
    // by calling login after registration
    const userData = await login(email, password, 'candidate');
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const updateUser = (updatedUser: Partial<User>) => {
    if (user) {
      const newUserData = { ...user, ...updatedUser };
      localStorage.setItem('user', JSON.stringify(newUserData));
      setUser(newUserData);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
