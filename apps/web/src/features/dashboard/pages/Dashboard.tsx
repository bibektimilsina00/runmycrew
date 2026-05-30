import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Loader2, X } from 'lucide-react'
import { GreetingRow }      from '../components/GreetingRow'
import { StatsGrid }        from '../components/StatsGrid'
import { PromptCard }       from '../components/PromptCard'
import { RecentRuns }       from '../components/RecentRuns'
import { SchedulePanel }    from '../components/SchedulePanel'
import { ConnectionsPanel } from '../components/ConnectionsPanel'
import { useDashboard }     from '../hooks/useDashboard'
import { APP_ROUTES }       from '@/shared/constants/routes'
import { useToast }         from '@/shared/components'
import { workflowAPI }      from '@/features/workflows/services/workflowAPI'
import { workflowKeys }     from '@/features/workflows/hooks/keys'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { streamCopilotChat } from '@/features/workflow-editor/services/copilotAPI'
import { editorAPI }        from '@/features/workflow-editor/services/editorAPI'
import type { DashboardStat } from '../services/dashboardAPI'

const LOADING_MESSAGES = [
  'Reading your request…',
  'Discovering the right nodes…',
  'Drafting the workflow…',
  'Wiring the connections…',
  'Validating fields…',
  'Tightening the bolts…',
  'Almost there…',
]

interface GeneratingCardProps {
  message: string
  onCancel: () => void
}

function GeneratingCard({ message, onCancel }: GeneratingCardProps) {
  return (
    <div className="flex items-center gap-3 rounded-[12px] border border-[var(--accent-line)] bg-[var(--accent-line)]/10 px-[18px] py-4">
      <Loader2 className="h-4 w-4 shrink-0 animate-spin text-[var(--accent)]" />
      <span className="flex-1 text-[13.5px] text-[var(--text)] transition-opacity duration-300">{message}</span>
      <button
        onClick={onCancel}
        className="inline-flex h-7 w-7 items-center justify-center rounded-[7px] text-[var(--text-mute)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
        title="Cancel"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}

const SKELETON_STATS: DashboardStat[] = [
  { label: 'Runs today',       value: '—', unit: '',   delta: '—', delta_dir: 'flat', spark: [] },
  { label: 'Success rate',     value: '—', unit: '%',  delta: '—', delta_dir: 'flat', spark: [] },
  { label: 'Time saved',       value: '—', unit: 'hr', delta: '—', delta_dir: 'flat', spark: [] },
  { label: 'Active workflows', value: '—', unit: '',   delta: '—', delta_dir: 'flat', spark: [] },
]

export function Dashboard() {
  const navigate = useNavigate()
  const { data } = useDashboard()
  const { toast } = useToast()
  const qc = useQueryClient()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  const [creating, setCreating] = useState(false)
  const [loadingMsgIdx, setLoadingMsgIdx] = useState(0)
  const abortRef = useRef<AbortController | null>(null)

  // Rotate loading messages while generating
  useEffect(() => {
    if (!creating) return
    const id = setInterval(
      () => setLoadingMsgIdx(i => (i + 1) % LOADING_MESSAGES.length),
      1800,
    )
    return () => clearInterval(id)
  }, [creating])

  const stats       = data?.stats       ?? SKELETON_STATS
  const recentRuns  = data?.recent_runs ?? []
  const schedules   = data?.schedules   ?? []
  const connections = data?.connections ?? []
  const totalToday  = data?.total_today ?? 0

  // Generate a workflow with Copilot from the dashboard prompt:
  // create the workflow → stream Copilot to a proposed graph → persist it →
  // only then navigate to the editor (so the user lands on a built workflow).
  const handlePrompt = async (prompt: string) => {
    setLoadingMsgIdx(0)
    setCreating(true)
    let createdId: string | null = null
    try {
      const name = prompt.slice(0, 60).trim() || 'New AI workflow'
      const wf = await workflowAPI.create({ name })
      createdId = wf.id

      const ctrl = new AbortController()
      abortRef.current = ctrl
      let proposed: { nodes: unknown[]; edges: unknown[] } | null = null
      const stream = streamCopilotChat(
        wf.id,
        { messages: [{ role: 'user', content: prompt }], graph: { nodes: [], edges: [] } },
        ctrl.signal,
      )
      for await (const ev of stream) {
        if (ev.type === 'workflow_proposed') {
          proposed = ev.graph as { nodes: unknown[]; edges: unknown[] }
        } else if (ev.type === 'error') {
          throw new Error(String(ev.message ?? 'Copilot error'))
        }
      }

      if (proposed) {
        // Fresh workflow → version_vector starts at 0.
        await editorAPI.saveGraph(wf.id, proposed, 0).catch(() => {})
      }
      qc.invalidateQueries({ queryKey: workflowKeys.lists(workspaceId) })
      navigate(`/workflows/${wf.id}`)
    } catch (e) {
      const err = e as Error
      if (err.name === 'AbortError') {
        // User cancelled — keep the empty workflow and drop them into the editor.
        if (createdId) navigate(`/workflows/${createdId}`)
      } else {
        toast(`Copilot failed: ${err.message || 'error'}`, { variant: 'err' })
      }
    } finally {
      abortRef.current = null
      setCreating(false)
    }
  }

  const cancelGenerate = () => abortRef.current?.abort()

  return (
    <div className="p-[24px_28px_28px] flex flex-col gap-[24px] max-w-[1240px] w-full mx-auto flex-1">
      <GreetingRow />

      <StatsGrid items={stats} />

      {creating ? (
        <GeneratingCard message={LOADING_MESSAGES[loadingMsgIdx]} onCancel={cancelGenerate} />
      ) : (
        <PromptCard onSubmit={handlePrompt} />
      )}

      <div className="grid grid-cols-[minmax(0,1fr)_320px] gap-[24px]">
        <RecentRuns
          items={recentRuns}
          totalToday={totalToday}
          onViewAll={() => navigate(APP_ROUTES.RUNS)}
        />
        <div className="flex flex-col gap-[16px]">
          <SchedulePanel
            items={schedules}
            onViewAll={() => navigate(APP_ROUTES.SCHEDULES)}
          />
          <ConnectionsPanel
            items={connections}
            totalActive={connections.filter(c => c.state === 'ok').length}
          />
        </div>
      </div>
    </div>
  )
}
