import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { useEffect } from 'react'
import { requestJson } from '@/lib/api/client'
import { WorkflowSchema } from '@/lib/api/contracts'
import { workflowKeys } from '@/features/dashboard/hooks/keys'
import { useWorkflowStore } from '@/stores/workflow-store'
import { useWorkspaceStore } from '@/stores/workspace-store'

/**
 * Hook to fetch a single workflow by ID and sync it with the workflow store.
 */
export function useWorkflowData() {
  const { id } = useParams<{ id: string }>()
  const loadWorkflow = useWorkflowStore((state) => state.loadWorkflow)
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  const query = useQuery({
    queryKey: workflowKeys.detail(id || '', workspaceId),
    queryFn: async ({ signal }) => {
      if (!id) throw new Error('Workflow ID is required')

      return requestJson(WorkflowSchema, {
        url: `/workflows/${id}`,
        method: 'GET',
        signal,
      })
    },
    enabled: !!id && !!workspaceId,
    staleTime: 1000 * 60 * 5, // 5 minutes stale time
  })

  // Sync with store when data is loaded
  useEffect(() => {
    if (query.data) {
      loadWorkflow(query.data)
    }
  }, [query.data, loadWorkflow])

  return query
}
