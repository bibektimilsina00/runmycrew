import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useToast } from '@/shared/components'
import { workflowAPI } from '@/features/workflows/services/workflowAPI'
import { workflowKeys } from '@/features/workflows/hooks/keys'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { useCopilotPendingStore } from '@/features/workflow-editor/stores/copilotPendingStore'

/**
 * Dashboard → Copilot handoff:
 * 1) create a fresh workflow (brief loading),
 * 2) park the prompt for the Copilot panel,
 * 3) navigate to the editor — the Copilot panel auto-sends it and streams there.
 */
export function useAIGenerator() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { toast } = useToast()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  const [creating, setCreating] = useState(false)

  const generate = async (prompt: string) => {
    setCreating(true)
    try {
      const name = prompt.slice(0, 60).trim() || 'New AI workflow'
      const wf = await workflowAPI.create({ name })
      qc.invalidateQueries({ queryKey: workflowKeys.lists(workspaceId) })
      useCopilotPendingStore.getState().set(prompt)
      navigate(`/workflows/${wf.id}`)
    } catch {
      toast('Could not create the workflow', { variant: 'err' })
    } finally {
      setCreating(false)
    }
  }

  return {
    creating,
    statusMessage: 'Spinning up your workflow…',
    generate,
  }
}
