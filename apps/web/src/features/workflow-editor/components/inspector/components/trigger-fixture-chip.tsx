import { useQuery } from '@tanstack/react-query'
import { Clock } from 'lucide-react'
import apiClient from '@/shared/utils/apiClient'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'

interface TriggerFixtureResponse {
  node_id: string
  source: string
  captured_at: string
  payload: Record<string, unknown>
}

interface Props {
  nodeId: string
}

/**
 * Status chip shown above the property list for any selected trigger
 * node. Surfaces the last captured event so the user knows whether a
 * manual `Run` will replay a real payload or fail-loud because no event
 * has ever fired.
 *
 * Lives entirely inside the inspector — `Run` itself does not change.
 * The backend's `WorkflowRunner` automatically injects the latest
 * fixture as `input_data` when the manual run carries no payload, so
 * clicking Run is "Replay" implicitly.
 */
export function TriggerFixtureChip({ nodeId }: Props) {
  const workflowId = useWorkflowEditorStore((s) => s.workflow?.id ?? null)

  const query = useQuery<TriggerFixtureResponse | null>({
    queryKey: ['trigger-fixture', workflowId, nodeId],
    queryFn: async () => {
      if (!workflowId) return null
      try {
        const res = await apiClient.get<TriggerFixtureResponse>(
          `/workflows/${workflowId}/triggers/${nodeId}/fixture`,
        )
        return res.data
      } catch (err) {
        const status = (err as { response?: { status?: number } })?.response?.status
        if (status === 404) return null
        throw err
      }
    },
    enabled: Boolean(workflowId && nodeId),
    staleTime: 1000 * 30,
  })

  if (query.isLoading) {
    return (
      <div className="mx-4 mt-3 h-7 animate-pulse rounded-md bg-[var(--surface)]" />
    )
  }

  // Empty state (no captured event yet) is intentionally not rendered —
  // it cluttered the inspector for nodes that hadn't seen a fire. The
  // chip only appears when there's something useful to show.
  if (!query.data) return null

  return (
    <div className="mx-4 mt-3 flex items-center gap-2 rounded-md border border-[var(--border-faint)] bg-[var(--surface)] px-3 py-2 text-[11px] text-[var(--text-mute)]">
      <Clock className="h-3.5 w-3.5 text-[var(--ok)]" />
      <span className="flex-1">
        Last event ·{' '}
        <span className="text-[var(--text)]">
          {formatRelative(query.data.captured_at)}
        </span>
      </span>
      <span className="text-[var(--text-faint)]">{query.data.source}</span>
    </div>
  )
}

function formatRelative(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return iso
  const diffSec = Math.max(0, Math.floor((Date.now() - then) / 1000))
  if (diffSec < 60) return `${diffSec}s ago`
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
  if (diffSec < 86_400) return `${Math.floor(diffSec / 3600)}h ago`
  return `${Math.floor(diffSec / 86_400)}d ago`
}
