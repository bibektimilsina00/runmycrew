import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface AuthUser {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
}

interface AuthState {
  token: string | null
  user: AuthUser | null
  isAuthenticated: boolean
  setToken: (token: string | null) => void
  setUser: (user: AuthUser | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      setToken: (token) => set({ token, isAuthenticated: !!token }),
      setUser: (user) => set({ user }),
      logout: () => {
        set({ token: null, user: null, isAuthenticated: false })
        // Clear workspace + collaboration state
        Promise.all([
          import('@/stores/workspace-store').then(m => m.useWorkspaceStore.getState().clearWorkspace()),
          import('@/stores/collaboration-store').then(m => m.useCollaborationStore.getState().reset()),
        ])
      },
    }),
    { name: 'fuse-auth-storage' }
  )
)
