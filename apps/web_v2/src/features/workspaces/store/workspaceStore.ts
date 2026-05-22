import { create } from 'zustand'
import { persist, type PersistOptions } from 'zustand/middleware'
import type { Workspace, WorkspaceWithRole, WorkspaceRole } from '../types/workspaceTypes'

interface WorkspaceState {
  currentWorkspaceId: string | null
  currentWorkspace: Workspace | null
  currentRole: WorkspaceRole | null
  workspaces: WorkspaceWithRole[]

  setCurrentWorkspace: (workspace: Workspace, role: WorkspaceRole) => void
  setWorkspaces: (workspaces: WorkspaceWithRole[]) => void
  clearWorkspace: () => void

  // Permission helpers
  canManageMembers: () => boolean
  canEdit: () => boolean
  isOwner: () => boolean
}

type PersistedSlice = Pick<WorkspaceState, 'currentWorkspaceId'>
type PersistConfig = PersistOptions<WorkspaceState, PersistedSlice>

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      currentWorkspaceId: null,
      currentWorkspace: null,
      currentRole: null,
      workspaces: [],

      setCurrentWorkspace: (workspace, role) =>
        set({ currentWorkspace: workspace, currentWorkspaceId: workspace.id, currentRole: role }),

      setWorkspaces: (workspaces) => set({ workspaces }),

      clearWorkspace: () =>
        set({ currentWorkspace: null, currentWorkspaceId: null, currentRole: null, workspaces: [] }),

      canManageMembers: () => {
        const role = get().currentRole
        return role === 'owner' || role === 'admin'
      },

      canEdit: () => {
        const role = get().currentRole
        return role === 'owner' || role === 'admin' || role === 'member'
      },

      isOwner: () => get().currentRole === 'owner',
    }),
    {
      name: 'fuse-workspace-v2',
      partialize: (state) => ({ currentWorkspaceId: state.currentWorkspaceId }),
    } satisfies PersistConfig,
  )
)
