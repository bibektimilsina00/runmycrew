import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { workspaceAPI } from '../services/workspaceAPI'
import { useWorkspaceStore } from '../store/workspaceStore'
import { workspaceKeys } from './keys'
import type { WorkspaceRole, WorkspaceWithRole } from '../types/workspaceTypes'

/** Fetch all workspaces the current user belongs to, auto-select current. */
export function useWorkspaces() {
  const setWorkspaces = useWorkspaceStore(s => s.setWorkspaces)
  const setCurrentWorkspace = useWorkspaceStore(s => s.setCurrentWorkspace)

  return useQuery({
    queryKey: workspaceKeys.lists(),
    queryFn: async ({ signal }) => {
      const workspaces = await workspaceAPI.listWorkspaces(signal)
      const normalized = workspaces.map(w => ({ ...w, avatar_url: w.avatar_url ?? null }))
      setWorkspaces(normalized)

      const savedId = useWorkspaceStore.getState().currentWorkspaceId
      const current =
        normalized.find(w => w.id === savedId) ??
        normalized.find(w => w.is_personal) ??
        normalized[0]
      if (current) setCurrentWorkspace(current, current.role)

      return normalized
    },
    staleTime: 1000 * 60,
  })
}

/** Create a new workspace and switch to it. */
export function useCreateWorkspace() {
  const queryClient = useQueryClient()
  const setCurrentWorkspace = useWorkspaceStore(s => s.setCurrentWorkspace)

  return useMutation({
    mutationFn: (name: string) => workspaceAPI.createWorkspace({ name }),
    onSuccess: (workspace) => {
      const normalized = { ...workspace, avatar_url: workspace.avatar_url ?? null }
      setCurrentWorkspace(normalized, normalized.role)
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}

/** Switch the active workspace (no API call — just store update). */
export function switchWorkspace(workspace: WorkspaceWithRole) {
  const normalized = { ...workspace, avatar_url: workspace.avatar_url ?? null }
  useWorkspaceStore.getState().setCurrentWorkspace(normalized, normalized.role)
}

/** Rename workspace — owner only. */
export function useUpdateWorkspace() {
  const queryClient = useQueryClient()
  const setCurrentWorkspace = useWorkspaceStore(s => s.setCurrentWorkspace)

  return useMutation({
    mutationFn: ({ workspaceId, name }: { workspaceId: string; name: string }) =>
      workspaceAPI.updateWorkspace(workspaceId, { name }),
    onSuccess: (updated) => {
      const normalized = { ...updated, avatar_url: updated.avatar_url ?? null }
      setCurrentWorkspace(normalized, normalized.role)
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}

/** Delete workspace — owner only, non-personal only. */
export function useDeleteWorkspace() {
  const queryClient = useQueryClient()
  const clearWorkspace = useWorkspaceStore(s => s.clearWorkspace)

  return useMutation({
    mutationFn: (workspaceId: string) => workspaceAPI.deleteWorkspace(workspaceId),
    onSuccess: async () => {
      clearWorkspace()
      await queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
      await queryClient.refetchQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}

/** Fetch members of a workspace. */
export function useWorkspaceMembers(workspaceId: string | null) {
  return useQuery({
    queryKey: workspaceKeys.members(workspaceId),
    queryFn: ({ signal }) => {
      if (!workspaceId) return []
      return workspaceAPI.listMembers(workspaceId, signal)
    },
    enabled: !!workspaceId,
    staleTime: 1000 * 30,
  })
}

/** Create an invite link for a workspace. */
export function useCreateInvite(workspaceId: string | null) {
  return useMutation({
    mutationFn: (data: { email: string; role: WorkspaceRole; send_email: boolean }) => {
      if (!workspaceId) throw new Error('No workspace selected')
      return workspaceAPI.createInvite(workspaceId, data)
    },
  })
}

/** Preview an invite before accepting (public — no auth needed). */
export function useInvitePreview(token: string | undefined) {
  return useQuery({
    queryKey: workspaceKeys.invite(token),
    queryFn: ({ signal }) => {
      if (!token) throw new Error('No token')
      return workspaceAPI.previewInvite(token, signal)
    },
    enabled: !!token,
    staleTime: 1000 * 60,
  })
}

/** Accept an invite — joins the workspace and refreshes list. */
export function useAcceptInvite(token: string | undefined) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => {
      if (!token) throw new Error('No token')
      return workspaceAPI.acceptInvite(token)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
      await queryClient.refetchQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}

/** Update a member's role. */
export function useUpdateMember(workspaceId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: WorkspaceRole }) => {
      if (!workspaceId) throw new Error('No workspace selected')
      return workspaceAPI.updateMember(workspaceId, userId, { role })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.members(workspaceId) })
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}

/** Remove a member from a workspace. */
export function useRemoveMember(workspaceId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userId: string) => {
      if (!workspaceId) {
        throw new Error('No workspace selected')
      }
      return workspaceAPI.removeMember(workspaceId, userId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.members(workspaceId) })
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}
