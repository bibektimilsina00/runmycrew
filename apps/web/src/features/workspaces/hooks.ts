import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { requestJson } from '@/lib/api/client'
import {
  WorkspaceInviteSchema,
  WorkspaceMemberSchema,
  WorkspaceWithRoleSchema,
  type WorkspaceRole,
  type WorkspaceWithRoleContract,
} from '@/lib/api/contracts'
import { useWorkspaceStore } from '@/stores/workspace-store'

export const workspaceKeys = {
  all: ['workspaces'] as const,
  lists: () => [...workspaceKeys.all, 'list'] as const,
  members: (workspaceId: string | null) => [...workspaceKeys.all, workspaceId, 'members'] as const,
}

const WorkspaceListSchema = z.array(WorkspaceWithRoleSchema)
const WorkspaceMemberListSchema = z.array(WorkspaceMemberSchema)

export function useWorkspaces() {
  const setWorkspaces = useWorkspaceStore(s => s.setWorkspaces)
  const setCurrentWorkspace = useWorkspaceStore(s => s.setCurrentWorkspace)

  return useQuery({
    queryKey: workspaceKeys.lists(),
    queryFn: async ({ signal }) => {
      const workspaces = await requestJson(WorkspaceListSchema, {
        url: '/workspaces/',
        method: 'GET',
        signal,
      })
      const normalized = workspaces.map(workspace => ({
        ...workspace,
        avatar_url: workspace.avatar_url ?? null,
      }))
      setWorkspaces(normalized)
      const selectedWorkspaceId = useWorkspaceStore.getState().currentWorkspaceId
      const current =
        normalized.find(w => w.id === selectedWorkspaceId) ??
        normalized.find(w => w.is_personal) ??
        normalized[0]
      if (current) setCurrentWorkspace(current, current.role)
      return workspaces
    },
    staleTime: 1000 * 60,
  })
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) =>
      requestJson(WorkspaceWithRoleSchema, {
        url: '/workspaces/',
        method: 'POST',
        data: { name },
      }),
    onSuccess: (workspace) => {
      const normalized = { ...workspace, avatar_url: workspace.avatar_url ?? null }
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
      useWorkspaceStore.getState().setCurrentWorkspace(normalized, normalized.role)
    },
  })
}

export function useWorkspaceMembers(workspaceId: string | null) {
  return useQuery({
    queryKey: workspaceKeys.members(workspaceId),
    queryFn: async ({ signal }) => {
      if (!workspaceId) return []
      return requestJson(WorkspaceMemberListSchema, {
        url: `/workspaces/${workspaceId}/members`,
        method: 'GET',
        signal,
      })
    },
    enabled: !!workspaceId,
    staleTime: 1000 * 30,
  })
}

export function useCreateWorkspaceInvite(workspaceId: string | null) {
  return useMutation({
    mutationFn: (data: { email: string; role: WorkspaceRole; send_email: boolean }) => {
      if (!workspaceId) throw new Error('Workspace is required')
      return requestJson(WorkspaceInviteSchema, {
        url: `/workspaces/${workspaceId}/invites`,
        method: 'POST',
        data,
      })
    },
  })
}

export function useInvitePreview(token: string | undefined) {
  return useQuery({
    queryKey: [...workspaceKeys.all, 'invite', token],
    queryFn: async ({ signal }) => {
      if (!token) throw new Error('Invite token is required')
      return requestJson(z.object({
        workspace_id: z.string().uuid(),
        workspace_name: z.string(),
        email: z.string(),
        role: z.enum(['owner', 'admin', 'member', 'viewer']),
        expires_at: z.string(),
        accepted_at: z.string().nullable().optional(),
      }), {
        url: `/workspaces/invites/${token}`,
        method: 'GET',
        signal,
      })
    },
    enabled: !!token,
    staleTime: 1000 * 60,
  })
}

export function useAcceptInvite(token: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      if (!token) throw new Error('Invite token is required')
      return requestJson(WorkspaceMemberSchema, {
        url: `/workspaces/invites/${token}/accept`,
        method: 'POST',
      })
    },
    onSuccess: async () => {
      // Invalidate and refetch workspaces — useWorkspaces() will auto-set the new workspace as current
      await queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
      await queryClient.refetchQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}

export function useUpdateWorkspaceMember(workspaceId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: WorkspaceRole }) => {
      if (!workspaceId) throw new Error('Workspace is required')
      return requestJson(WorkspaceMemberSchema, {
        url: `/workspaces/${workspaceId}/members/${userId}`,
        method: 'PATCH',
        data: { role },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.members(workspaceId) })
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}

export function useRemoveWorkspaceMember(workspaceId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => {
      if (!workspaceId) throw new Error('Workspace is required')
      return requestJson(z.any(), {
        url: `/workspaces/${workspaceId}/members/${userId}`,
        method: 'DELETE',
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.members(workspaceId) })
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}

export function switchWorkspace(workspace: WorkspaceWithRoleContract) {
  const normalized = { ...workspace, avatar_url: workspace.avatar_url ?? null }
  // Reset collaboration state when switching workspaces
  import('@/stores/collaboration-store').then(m => m.useCollaborationStore.getState().reset())
  useWorkspaceStore.getState().setCurrentWorkspace(normalized, normalized.role)
}
