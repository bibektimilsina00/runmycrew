import { useRunsStore } from '@/features/runs/store/runsStore'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'

export type ExecutionStatus = 'running' | 'completed' | 'failed' | null

/**
 * Derives a node's execution status from the current workflow's latest run.
 *
 * Source of truth is the per-node lifecycle map (`nodeStatuses`) populated
 * by `useRunStream` from the engine's `node_started` / `node_completed` /
 * `node_failed` events. Falls back to log scanning only when no explicit
 * status was recorded — that's the case for very old runs persisted before
 * v3 of the runs store + the unlikely path where the WS dropped a status
 * event but logs still landed.
 */
export function useNodeExecutionStatus(nodeId: string): ExecutionStatus {
  const workflowId = useWorkflowEditorStore((s) => s.workflow?.id ?? null)
  return useRunsStore((s) => {
    if (!workflowId) return null
    const slice = s.byWorkflow[workflowId]
    if (!slice) return null
    const latest = slice.runs[slice.runs.length - 1]
    if (!latest) return null

    const explicit = latest.nodeStatuses?.[nodeId]
    if (explicit) return explicit

    let touched = false
    for (const log of latest.logs) {
      if (log.nodeId !== nodeId) continue
      touched = true
      if (log.payload && 'error' in log.payload) return 'failed'
      if (log.payload && 'output' in log.payload) return 'completed'
    }

    if (latest.status === 'failed' && touched) return 'failed'
    if (latest.status === 'running' && touched) return 'running'
    return null
  })
}
