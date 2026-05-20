import { create } from 'zustand'
import { persist, type PersistOptions } from 'zustand/middleware'

export type WorkspaceRole = 'owner' | 'admin' | 'member' | 'viewer'

export interface Workspace {
  id: string
  name: string
  slug: string
  owner_id: string
  is_personal: boolean
  avatar_url: string | null
  plan: string
  created_at: string
  updated_at: string
}

export interface WorkspaceWithRole extends Workspace {
  role: WorkspaceRole
  member_count: number
}

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

type WorkspacePersistedState = Pick<WorkspaceState, 'currentWorkspaceId'>
type WorkspacePersistOptions = PersistOptions<WorkspaceState, WorkspacePersistedState>

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
      name: 'fuse-workspace',
      partialize: (state) => ({ currentWorkspaceId: state.currentWorkspaceId }),
    } satisfies WorkspacePersistOptions,
  )
)
