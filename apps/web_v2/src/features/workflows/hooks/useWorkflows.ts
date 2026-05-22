import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { workflowAPI } from '../services/workflowAPI'
import { workflowKeys } from './keys'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import type { WorkflowWithStats } from '../types/workflowTypes'

const ADJECTIVES = [
  'Swift', 'Smart', 'Silent', 'Dynamic', 'Clever', 'Bright', 'Agile', 'Fluid', 'Nimble', 'Bold', 'Lucid', 'Vivid', 'Rapid',
  'Quantum', 'Neural', 'Cyber', 'Magic', 'Hyper', 'Super', 'Turbo', 'Atomic', 'Cosmic', 'Stealth', 'Phantom', 'Neon', 'Digital', 'Sync', 'Macro', 'Prime', 'Elite', 'Pro', 'Ultra'
]
const NOUNS = [
  'Agent', 'Flow', 'Bot', 'Process', 'Worker', 'Task', 'Runner', 'Engine', 'Pipeline', 'Routine', 'System', 'Logic',
  'Network', 'Node', 'Hub', 'Grid', 'Matrix', 'Nexus', 'Core', 'Link', 'Chain', 'Wave', 'Stream', 'Pulse', 'Spark', 'Brain', 'Mind', 'Wizard', 'Ninja', 'Pilot', 'Driver', 'Scout'
]

/**
 * Hook to fetch all workflows for the current workspace with stats.
 */
export function useWorkflows() {
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  return useQuery({
    queryKey: workflowKeys.lists(workspaceId),
    queryFn: async ({ signal }) => {
      const workflows = await workflowAPI.listWithStats(signal)
      // Sort by position (ascending), then created_at (descending)
      return workflows.sort((a, b) => {
        const posA = a.position ?? 0
        const posB = b.position ?? 0
        if (posA !== posB) return posA - posB
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      })
    },
    enabled: !!workspaceId,
    staleTime: 1000 * 30, // 30 seconds
  })
}

/**
 * Hook to create a new workflow.
 */
export function useCreateWorkflow() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  return useMutation({
    mutationFn: async ({ name, folderId, position, color }: { name?: string; folderId?: string | null; position?: number; color?: string | null } = {}) => {
      let finalName = name
      if (!finalName || finalName === 'Untitled Workflow') {
        const adj = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)]
        const noun = NOUNS[Math.floor(Math.random() * NOUNS.length)]
        finalName = `${adj} ${noun}`
      }

      const workflows = queryClient.getQueryData<WorkflowWithStats[]>(workflowKeys.lists(workspaceId)) || []
      const defaultPos = position ?? (workflows.length > 0 ? Math.min(...workflows.map(w => w.position ?? 0)) - 1 : 0)

      return workflowAPI.create({ name: finalName, folderId, position: defaultPos, color })
    },
    onSuccess: (newWorkflow) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists(workspaceId) })
      queryClient.setQueryData(workflowKeys.detail(newWorkflow.id, workspaceId), newWorkflow)
      navigate(`/workflows/${newWorkflow.id}`)
    },
  })
}

/**
 * Hook to update an existing workflow.
 */
interface WorkflowUpdateInput {
  id: string
  name?: string
  description?: string | null
  folder_id?: string | null
  position?: number
  is_active?: boolean
  color?: string | null
  graph?: unknown
  env?: Record<string, string> | null
  expected_version?: number
  silent?: boolean
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  return useMutation({
    mutationFn: async ({ id, silent, ...data }: WorkflowUpdateInput) => {
      const result = await workflowAPI.update(id, data)
      return { ...result, silent }
    },
    onSuccess: (updatedWorkflow) => {
      if (updatedWorkflow.silent) return
      
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists(workspaceId) })
      queryClient.setQueryData(workflowKeys.detail(updatedWorkflow.id, workspaceId), updatedWorkflow)
    },
  })
}

/**
 * Hook to duplicate a workflow.
 */
export function useDuplicateWorkflow() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  return useMutation({
    mutationFn: (id: string) => workflowAPI.duplicate(id),
    onSuccess: (newWorkflow) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists(workspaceId) })
      queryClient.setQueryData(workflowKeys.detail(newWorkflow.id, workspaceId), newWorkflow)
      navigate(`/workflows/${newWorkflow.id}`)
    },
  })
}

/**
 * Hook to batch update workflows (position/folder).
 */
export function useBatchUpdateWorkflows() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  return useMutation({
    mutationFn: (data: { updates: { id: string; folder_id?: string | null; position?: number | null; color?: string | null }[] }) =>
      workflowAPI.batchUpdate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists(workspaceId) })
    },
  })
}

/**
 * Hook to delete a workflow.
 */
export function useDeleteWorkflow() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  return useMutation({
    mutationFn: (id: string) => workflowAPI.delete(id),
    onSuccess: (_, id) => {
      queryClient.setQueryData(workflowKeys.lists(workspaceId), (oldData: WorkflowWithStats[] | undefined) => {
        return oldData?.filter((w) => w.id !== id)
      })
      queryClient.removeQueries({ queryKey: workflowKeys.detail(id, workspaceId) })
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists(workspaceId) })
    },
  })
}
