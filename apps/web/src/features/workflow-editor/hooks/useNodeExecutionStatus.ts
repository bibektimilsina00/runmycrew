import { useRunsStore } from '@/features/runs/store/runsStore'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import { useListenState } from './useHostedListen'

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
  // A hosted trigger (Chat App / Form) with an open listen is "running":
  // the graph is live and waiting on the visitor. Keeps the node pulsing
  // between submissions, matching the action bar's "Listening…" state.
  const listeningHere = useListenState(
    (s) => !!workflowId && s.activeFor === workflowId && s.nodeId === nodeId,
  )
  const runInFlight = useRunsStore((s) => {
    if (!workflowId) return false
    const latest = s.byWorkflow[workflowId]?.runs.at(-1)
    return latest?.status === 'running'
  })
  const runStatus = useRunsStore((s) => {
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
  // While an execution is actually flowing, the real per-node lifecycle
  // wins — the trigger completes and downstream nodes light up in turn.
  // The listening pulse only covers the idle gaps between submissions.
  if (runInFlight) return runStatus
  if (listeningHere) return 'running'
  return runStatus
}
