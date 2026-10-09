import type { User, AuthResponse } from '@/lib/api/types'

export interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  login: (email: string, password: string) => Promise<AuthResponse>
  signup: (name: string, email: string, password: string) => Promise<AuthResponse>
  logout: () => Promise<void>
}
