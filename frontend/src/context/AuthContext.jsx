import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('health_auth_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('health_auth_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function initAuth() {
      const storedToken = localStorage.getItem('health_auth_token');
      if (storedToken) {
        try {
          const userData = await api.getMe();
          if (userData) {
            setUser(userData);
            localStorage.setItem('health_auth_user', JSON.stringify(userData));
          }
        } catch (err) {
          // Only log out if explicit 401 Unauthorized / invalid token
          const msg = err.message || '';
          if (msg.includes('401') || msg.includes('Invalid') || msg.includes('expired') || msg.includes('Unauthorized')) {
            console.warn('Session expired or invalid token', err);
            localStorage.removeItem('health_auth_token');
            localStorage.removeItem('health_auth_user');
            setToken(null);
            setUser(null);
          } else {
            console.warn('Network issue while verifying session; maintaining cached auth:', err);
          }
        }
      }
      setLoading(false);
    }
    initAuth();
  }, []);

  const login = async (email, password) => {
    const res = await api.signin(email, password);
    if (res.access_token) {
      localStorage.setItem('health_auth_token', res.access_token);
      if (res.user) {
        localStorage.setItem('health_auth_user', JSON.stringify(res.user));
        setUser(res.user);
      }
      setToken(res.access_token);
    }
    return res;
  };

  const signup = async (name, email, password) => {
    const res = await api.signup(name, email, password);
    if (res.access_token) {
      localStorage.setItem('health_auth_token', res.access_token);
      if (res.user) {
        localStorage.setItem('health_auth_user', JSON.stringify(res.user));
        setUser(res.user);
      }
      setToken(res.access_token);
    }
    return res;
  };

  const logout = async () => {
    try {
      await api.signout();
    } catch (e) {
      // ignore
    }
    localStorage.removeItem('health_auth_token');
    localStorage.removeItem('health_auth_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        loading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
