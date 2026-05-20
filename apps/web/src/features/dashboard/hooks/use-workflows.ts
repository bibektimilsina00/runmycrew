import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { requestJson } from '@/lib/api/client'
import { WorkflowSchema, type Workflow, type WorkflowBatchUpdate } from '@/lib/api/contracts'
import { workflowKeys } from '@/features/dashboard/hooks/keys'

const WorkflowListSchema = z.array(WorkflowSchema)


/**
 * Hook to fetch all workflows for the dashboard list.
 */
export function useWorkflows() {
  return useQuery({
    queryKey: workflowKeys.lists(),
    queryFn: async ({ signal }) => {
      const workflows = await requestJson(WorkflowListSchema, {
        url: '/workflows/',
        method: 'GET',
        signal,
      })

      // Sort by position (ascending), then created_at (descending)
      return workflows.sort((a, b) => {
        const posA = a.position ?? 0
        const posB = b.position ?? 0
        if (posA !== posB) return posA - posB
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      })
    },
    staleTime: 1000 * 60,
  })
}

const ADJECTIVES = [
  'Swift', 'Smart', 'Silent', 'Dynamic', 'Clever', 'Bright', 'Agile', 'Fluid', 'Nimble', 'Bold', 'Lucid', 'Vivid', 'Rapid',
  'Quantum', 'Neural', 'Cyber', 'Magic', 'Hyper', 'Super', 'Turbo', 'Atomic', 'Cosmic', 'Stealth', 'Phantom', 'Neon', 'Digital', 'Sync', 'Macro', 'Prime', 'Elite', 'Pro', 'Ultra'
]
const NOUNS = [
  'Agent', 'Flow', 'Bot', 'Process', 'Worker', 'Task', 'Runner', 'Engine', 'Pipeline', 'Routine', 'System', 'Logic',
  'Network', 'Node', 'Hub', 'Grid', 'Matrix', 'Nexus', 'Core', 'Link', 'Chain', 'Wave', 'Stream', 'Pulse', 'Spark', 'Brain', 'Mind', 'Wizard', 'Ninja', 'Pilot', 'Driver', 'Scout'
]

/**
 * Hook to create a new workflow.
 */
export function useCreateWorkflow() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: async (name?: string) => {
      let finalName = name
      if (!finalName || finalName === 'Untitled Workflow') {
        const adj = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)]
        const noun = NOUNS[Math.floor(Math.random() * NOUNS.length)]
        finalName = `${adj} ${noun}`
      }

      const workflows = queryClient.getQueryData<Workflow[]>(workflowKeys.lists()) || []
      const minPos = workflows.length > 0 ? Math.min(...workflows.map(w => w.position ?? 0)) : 0
      const position = minPos - 1

      return requestJson(WorkflowSchema, {
        url: '/workflows/',
        method: 'POST',
        data: { name: finalName, position },
      })
    },
    onSuccess: (newWorkflow) => {
      // Instantly update the cache so it appears at the top of the sidebar immediately
      queryClient.setQueryData(workflowKeys.lists(), (oldData: Workflow[] | undefined) => {
        return oldData ? [newWorkflow, ...oldData] : [newWorkflow]
      })
      
      navigate(`/workflows/${newWorkflow.id}`)
    },
  })
}

/**
 * Hook to update an existing workflow.
 */
export function useUpdateWorkflow() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, silent, ...data }: Partial<Workflow> & { id: string, silent?: boolean }) => {
      const result = await requestJson(WorkflowSchema, {
        url: `/workflows/${id}`,
        method: 'PUT',
        data,
      })
      return { ...result, silent }
    },
    onSuccess: (updatedWorkflow) => {
      if (updatedWorkflow.silent) return
      
      queryClient.setQueryData(workflowKeys.lists(), (oldData: Workflow[] | undefined) => {
        return oldData?.map((w) => (w.id === updatedWorkflow.id ? updatedWorkflow : w))
      })
    },
  })
}

/**
 * Hook to duplicate a workflow.
 */
export function useDuplicateWorkflow() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: async (id: string) => {
      return requestJson(WorkflowSchema, {
        url: `/workflows/${id}/duplicate`,
        method: 'POST',
      })
    },
    onSuccess: (newWorkflow) => {
      queryClient.setQueryData(workflowKeys.lists(), (old: Workflow[] | undefined) =>
        old ? [newWorkflow, ...old] : [newWorkflow]
      )
      navigate(`/workflows/${newWorkflow.id}`)
    },
  })
}

/**
 * Hook to batch update workflows (position/folder).
 */
export function useBatchUpdateWorkflows() {
  return useMutation({
    mutationFn: async (data: WorkflowBatchUpdate) => {
      return requestJson(z.any(), {
        url: '/workflows/batch',
        method: 'PATCH',
        data,
      })
    },
  })
}

/**
 * Hook to delete a workflow.
 */
export function useDeleteWorkflow() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      return requestJson(z.any(), {
        url: `/workflows/${id}`,
        method: 'DELETE',
      })
    },
    onSuccess: (_, id) => {
      queryClient.setQueryData(workflowKeys.lists(), (oldData: Workflow[] | undefined) => {
        return oldData?.filter((w) => w.id !== id)
      })
    },
  })
}
