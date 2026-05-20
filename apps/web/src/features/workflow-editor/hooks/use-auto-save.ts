import { useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useWorkflowStore } from '@/stores/workflow-store'
import { useUpdateWorkflow } from '@/features/dashboard/hooks/use-workflows'

/**
 * Hook that automatically persists workflow changes to the backend.
 * Uses debouncing to ensure silent background saving.
 */
export function useAutoSave() {
  const { id } = useParams<{ id: string }>()
  const { nodes, edges, workflowVersion, markSaved } = useWorkflowStore()
  const { mutate } = useUpdateWorkflow()
  
  const lastSavedRef = useRef<string>('')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!id || nodes.length === 0) return

    const currentGraph = JSON.stringify({ nodes, edges })
    
    // Skip if it's the same as what we just saved (or initial load)
    if (lastSavedRef.current === currentGraph) return

    // Clear existing timer
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    // Set a new timer to save after 1.5s of silence
    timerRef.current = setTimeout(() => {
      mutate({
        id,
        graph: { nodes, edges },
        expected_version: workflowVersion,
        silent: true // Custom flag to prevent UI refreshes
      }, {
        onSuccess: (workflow) => {
          markSaved(workflow.version_vector ?? workflowVersion)
          lastSavedRef.current = currentGraph
        },
      })
    }, 1500)

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [id, nodes, edges, mutate, workflowVersion, markSaved])
}
