import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '@/lib/api/client'
import type { User, AuthResponse } from '@/lib/api/types'
import type { AuthContextType } from '../types'

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const savedUser = localStorage.getItem('health_auth_user')
      return savedUser ? JSON.parse(savedUser) : null
    } catch {
      return null
    }
  })
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('health_auth_token'))
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    async function initAuth() {
      const storedToken = localStorage.getItem('health_auth_token')
      if (storedToken) {
        try {
          const userData = await api.getMe()
          if (userData) {
            setUser(userData)
            localStorage.setItem('health_auth_user', JSON.stringify(userData))
          }
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : String(err)
          if (
            msg.includes('401') ||
            msg.includes('Invalid') ||
            msg.includes('expired') ||
            msg.includes('Unauthorized')
          ) {
            console.warn('Session expired or invalid token', err)
            localStorage.removeItem('health_auth_token')
            localStorage.removeItem('health_auth_user')
            setToken(null)
            setUser(null)
          } else {
            console.warn('Network issue while verifying session; maintaining cached auth:', err)
          }
        }
      }
      setLoading(false)
    }
    initAuth()
  }, [])

  const login = async (email: string, password: string): Promise<AuthResponse> => {
    const res = await api.signin(email, password)
    if (res.access_token) {
      localStorage.setItem('health_auth_token', res.access_token)
      if (res.user) {
        localStorage.setItem('health_auth_user', JSON.stringify(res.user))
        setUser(res.user)
      }
      setToken(res.access_token)
    }
    return res
  }

  const signup = async (name: string, email: string, password: string): Promise<AuthResponse> => {
    const res = await api.signup(name, email, password)
    if (res.access_token) {
      localStorage.setItem('health_auth_token', res.access_token)
      if (res.user) {
        localStorage.setItem('health_auth_user', JSON.stringify(res.user))
        setUser(res.user)
      }
      setToken(res.access_token)
    }
    return res
  }

  const logout = async (): Promise<void> => {
    try {
      await api.signout()
    } catch {
      // ignore
    }
    localStorage.removeItem('health_auth_token')
    localStorage.removeItem('health_auth_user')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: Boolean(user),
        loading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
