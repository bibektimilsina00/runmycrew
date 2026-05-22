import { create } from 'zustand'
import type { User } from '../types/authType'

interface AuthStoreState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  setToken: (token: string | null) => void
  setUser: (user: User | null) => void
  setLoading: (isLoading: boolean) => void
  setError: (error: string | null) => void
  logout: () => void
}

/**
 * Helper to safely fetch token on initial load.
 */
const getInitialToken = (): string | null => {
  try {
    return localStorage.getItem('fuse-auth-token')
  } catch {
    return null
  }
}

/**
 * Zustand store to manage and access global authentication state.
 */
export const useAuthStore = create<AuthStoreState>((set) => ({
  token: getInitialToken(),
  user: null,
  isAuthenticated: !!getInitialToken(),
  isLoading: false,
  error: null,

  setToken: (token) => {
    try {
      if (token) {
        localStorage.setItem('fuse-auth-token', token)
      } else {
        localStorage.removeItem('fuse-auth-token')
      }
    } catch {
      // Handle sandboxed/private browser environments where storage access is blocked
    }
    set({ token, isAuthenticated: !!token })
  },

  setUser: (user) => set({ user }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  logout: () => {
    try {
      localStorage.removeItem('fuse-auth-token')
    } catch {
      // Ignore storage errors on sandbox
    }
    set({ token: null, user: null, isAuthenticated: false, error: null })
  },
}))
