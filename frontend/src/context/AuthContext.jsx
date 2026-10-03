import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('hia_auth_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function initAuth() {
      const storedToken = localStorage.getItem('hia_auth_token');
      if (storedToken) {
        try {
          const userData = await api.getMe();
          setUser(userData);
        } catch (err) {
          console.warn('Session expired or invalid token', err);
          localStorage.removeItem('hia_auth_token');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    }
    initAuth();
  }, []);

  const login = async (email, password) => {
    const res = await api.signin(email, password);
    if (res.access_token) {
      localStorage.setItem('hia_auth_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    }
    return res;
  };

  const signup = async (name, email, password) => {
    const res = await api.signup(name, email, password);
    if (res.access_token) {
      localStorage.setItem('hia_auth_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    }
    return res;
  };

  const logout = async () => {
    try {
      await api.signout();
    } catch (e) {
      // ignore
    }
    localStorage.removeItem('hia_auth_token');
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
