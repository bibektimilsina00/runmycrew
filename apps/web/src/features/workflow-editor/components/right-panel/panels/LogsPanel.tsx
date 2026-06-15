import React, { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Loader2, Terminal, Trash2, XCircle } from 'lucide-react'
import { cn } from '@/lib/cn'
import { getIcon } from '../../../utils/icon-map'
import { Empty } from '@/shared/components'
import { useRunsStore, useWorkflowRuns, type Run, type RunLog } from '@/features/runs/store/runsStore'
import { useRunStream } from '@/features/runs/hooks/useRunStream'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'
import {
  ErrorView,
  JsonInspector,
  LogRow,
  WaitingView,
  isNodeCompletionLog,
  type NodeInfo,
  type Tab,
} from './logs'

/**
 * Logs panel — split view: a `Runs` list on the left, an inspector on the
 * right that shows either the JSON tree/code of the selected log's
 * input/output or, for failed nodes, an `ErrorView` with a "Fix with
 * Copilot" call-to-action.
 *
 * The panel reads execution data from `useWorkflowRuns(workflowId)` — runs
 * are scoped per workflow so switching workflows preserves history.
 */
export function LogsPanel() {
  const workflowId = useWorkflowEditorStore((s) => s.workflow?.id ?? null)
  const slice = useWorkflowRuns(workflowId)
  const { runs, activeExecutionId, selectedLogId } = slice
  const setSelectedLogId = useRunsStore((s) => s.setSelectedLogId)
  const clearRuns = useRunsStore((s) => s.clearRuns)
  const setActiveExecutionId = useRunsStore((s) => s.setActiveExecutionId)

  const nodes = useWorkflowEditorStore((s) => s.nodes)
  const nodeDefinitions = useWorkflowEditorStore((s) => s.nodeDefinitions)
  const selectNode = useWorkflowEditorStore((s) => s.setSelectedNodeId)

  useRunStream(workflowId, activeExecutionId)

  // Client-side expiry sweep — Redis drops the slot when TTL elapses but no
  // server event is pushed to the WS, so the run row would otherwise stay
  // "waiting" forever in the UI. Tick every second, flip any waiting run
  // whose deadline has passed to "failed" and record an expiry log so the
  // user can tell the difference between a still-listening run and a dead
  // one.
  useEffect(() => {
    if (!workflowId) return
    const tick = () => {
      const state = useRunsStore.getState()
      const wf = state.byWorkflow[workflowId]
      if (!wf) return
      const now = Date.now()
      for (const r of wf.runs) {
        if (r.status !== 'waiting') continue
        // Sweep regardless of whether `listenStartedAt` / `listenTtlSeconds`
        // are populated. Older runs persisted before those fields existed
        // would otherwise sit in "waiting" forever because the deadline
        // check below would always short-circuit. Treat any run that's
        // missing listen metadata as already-expired so the next paint
        // shows it as failed, matching what we already display via
        // WaitingView's countdown.
        const hasMeta = !!r.listenStartedAt && r.listenTtlSeconds != null
        if (hasMeta) {
          const deadline = Date.parse(r.listenStartedAt!) + (r.listenTtlSeconds as number) * 1000
          if (now < deadline) continue
        }
        // Order matters: setStatus first, then appendLog. NEVER call
        // setWaiting here — it hard-resets the row's status to 'waiting'
        // by design (used at slot-open time), which would immediately
        // revert the failed state we just set.
        state.setStatus(workflowId, r.executionId, 'failed')
        state.appendLog(workflowId, r.executionId, {
          id: `${r.executionId}-expired`,
          nodeId: r.listenNodeId ?? null,
          level: 'error',
          message: `Listen slot expired — no ${r.waitingFor ?? 'event'} arrived within the TTL window.`,
          payload: {
            error: `Listen slot expired — no ${r.waitingFor ?? 'event'} arrived within the TTL window. Check Meta webhook delivery + try again.`,
          },
          timestamp: new Date().toISOString(),
        })
      }
    }
    tick()
    const id = window.setInterval(tick, 1000)
    return () => window.clearInterval(id)
  }, [workflowId])

  const [tab, setTab] = useState<Tab>('output')

  const nodeInfoById = useMemo(() => {
    const map = new Map<string, NodeInfo>()
    for (const n of nodes) {
      const def = nodeDefinitions.find((d) => d.type === n.type)
      const label = (n.data?.label as string | undefined) || def?.name || n.id
      map.set(n.id, {
        label,
        icon: def?.icon ?? 'Box',
        color: def?.color,
      })
    }
    return map
  }, [nodes, nodeDefinitions])

  const selectedLog = useMemo<RunLog | null>(() => {
    if (!selectedLogId) return null
    for (const r of runs) {
      const l = r.logs.find((x) => x.id === selectedLogId)
      if (l) return l
      // Synthetic "waiting" pseudo-log is not in r.logs — materialize on
      // demand so SelectedLogView can render WaitingView from the run's
      // listen metadata.
      if (
        selectedLogId === `${r.executionId}-waiting` &&
        r.status === 'waiting' &&
        r.listenNodeId
      ) {
        return {
          id: selectedLogId,
          nodeId: r.listenNodeId,
          level: 'info',
          message: `Listening for ${r.waitingFor ?? 'next event'}…`,
          payload: {
            waiting: {
              waitingFor: r.waitingFor ?? 'next event',
              targetId: r.listenTargetId ?? null,
              ttlSeconds: r.listenTtlSeconds ?? null,
              startedAt: r.listenStartedAt ?? null,
            },
          },
          timestamp: r.listenStartedAt ?? new Date().toISOString(),
        }
      }
    }
    return null
  }, [selectedLogId, runs])

  const visible = useMemo(() => {
    if (!selectedLog) return null
    if (tab === 'output') {
      return (selectedLog.payload?.output as unknown) ?? (selectedLog.payload?.error as unknown) ?? null
    }
    return (selectedLog.payload?.input as unknown) ?? (selectedLog.payload?.data_in as unknown) ?? null
  }, [selectedLog, tab])

  if (runs.length === 0) {
    return (
      <Empty
        icon={<Terminal />}
        title="No run logs"
        description="Run the workflow to see execution logs here."
        className="h-full"
      />
    )
  }

  return (
    <div className="flex h-full min-h-0">
      <RunsList
        runs={runs}
        selectedLogId={selectedLogId}
        nodeInfoById={nodeInfoById}
        onSelectLog={(log) => {
          if (workflowId) setSelectedLogId(workflowId, log.id)
          if (log.nodeId) selectNode(log.nodeId)
        }}
        onClear={() => {
          if (!workflowId) return
          clearRuns(workflowId)
          setActiveExecutionId(workflowId, null)
        }}
      />

      <SelectedLogView
        selectedLog={selectedLog}
        nodeInfoById={nodeInfoById}
        tab={tab}
        setTab={setTab}
        payload={visible}
      />
    </div>
  )
}

// ── Runs list ────────────────────────────────────────────────────────────────

interface RunsListProps {
  runs: Run[]
  selectedLogId: string | null
  nodeInfoById: Map<string, NodeInfo>
  onSelectLog: (log: RunLog) => void
  onClear: () => void
}

function RunsList({
  runs, selectedLogId, nodeInfoById, onSelectLog, onClear,
}: RunsListProps) {
  return (
    <div className="flex w-[240px] shrink-0 flex-col border-r border-[var(--border-faint)]">
      <div className="flex h-[36px] shrink-0 items-center justify-between border-b border-[var(--border-faint)] px-3 py-1.5">
        <span className="text-[12px] font-medium text-[var(--text)]">Runs</span>
        <button
          onClick={onClear}
          className="flex items-center gap-1 rounded-[6px] px-2 py-1 text-[11.5px] text-[var(--text-mute)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
          title="Clear runs"
        >
          <Trash2 className="h-3 w-3" /> Clear
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        {runs
          .map((run, runIdx) => ({ run, runNumber: runIdx + 1 }))
          .slice()
          .reverse()
          .map(({ run, runNumber }) => {
            const completions = run.logs.filter(isNodeCompletionLog)
            return (
              <div key={run.executionId} className="mb-4 last:mb-0">
                <div className="flex items-center gap-2 px-1 pb-1">
                  {run.status === 'running' || run.status === 'waiting' ? (
                    <Loader2 className="h-3 w-3 animate-spin text-[var(--text-faint)]" />
                  ) : run.status === 'failed' || run.status === 'cancelled' ? (
                    <XCircle className="h-3 w-3 text-[var(--err)]" />
                  ) : (
                    <CheckCircle2 className="h-3 w-3 text-[var(--ok,#22c55e)]" />
                  )}
                  <span className="text-[11px] font-semibold text-[var(--text-mute)]">
                    Run #{runNumber}
                  </span>
                  <span className="text-[10.5px] text-[var(--text-faint)]">{run.status}</span>
                </div>
                {(() => {
                  // A run that's still waiting renders its trigger node as a
                  // synthetic "waiting" row so the user sees *which* node is
                  // listening + can click into WaitingView in the right pane.
                  const waitingRow =
                    run.status === 'waiting' && run.listenNodeId ? (
                      <WaitingRow
                        key={`${run.executionId}-waiting`}
                        runExecutionId={run.executionId}
                        nodeId={run.listenNodeId}
                        waitingFor={run.waitingFor ?? 'next event'}
                        nodeInfo={
                          nodeInfoById.get(run.listenNodeId) ?? {
                            label: run.listenNodeId,
                            icon: 'Box',
                          }
                        }
                        selected={
                          selectedLogId === `${run.executionId}-waiting`
                        }
                        onClick={() =>
                          onSelectLog({
                            id: `${run.executionId}-waiting`,
                            nodeId: run.listenNodeId!,
                            level: 'info',
                            message: `Listening for ${run.waitingFor ?? 'next event'}…`,
                            payload: null,
                            timestamp: new Date().toISOString(),
                          })
                        }
                      />
                    ) : null

                  if (waitingRow || completions.length > 0) {
                    return (
                      <div className="flex flex-col gap-1.5">
                        {waitingRow}
                        {completions.map((log) => {
                          const info = nodeInfoById.get(log.nodeId!) ?? {
                            label: log.message || log.nodeId!,
                            icon: 'Box',
                          }
                          return (
                            <LogRow
                              key={log.id}
                              log={log}
                              selected={selectedLogId === log.id}
                              nodeInfo={info}
                              onClick={() => onSelectLog(log)}
                            />
                          )
                        })}
                      </div>
                    )
                  }
                  return (
                    <div className="px-2 py-1 text-[11.5px] italic text-[var(--text-faint)]">
                      {run.status === 'running' ? 'Executing…' : 'No node logs'}
                    </div>
                  )
                })()}
              </div>
            )
          })}
      </div>
    </div>
  )
}

// ── Waiting row (synthetic, while a listen slot is open) ─────────────────────

interface WaitingRowProps {
  runExecutionId: string
  nodeId: string
  waitingFor: string
  nodeInfo: NodeInfo
  selected: boolean
  onClick: () => void
}

function WaitingRow({ nodeInfo, waitingFor, selected, onClick }: WaitingRowProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex w-full items-center gap-2 rounded-[8px] px-2 py-1.5 text-left text-[12px] transition-colors',
        selected
          ? 'bg-[var(--surface-2)] text-[var(--text)]'
          : 'text-[var(--text-mute)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
      )}
    >
      <div
        className="flex size-[20px] shrink-0 items-center justify-center rounded-[5px]"
        style={{ background: nodeInfo.color ?? 'var(--surface-3)' }}
      >
        {React.cloneElement(
          getIcon(nodeInfo.icon) as React.ReactElement<{ className?: string }>,
          { className: 'size-[12px] text-white' },
        )}
      </div>
      <span className="flex-1 truncate font-medium text-[var(--text)]" title={nodeInfo.label}>
        {nodeInfo.label}
      </span>
      <span className="flex shrink-0 items-center gap-1 text-[10.5px] text-[var(--text-faint)]">
        <Loader2 className="h-3 w-3 animate-spin" />
        <span className="truncate max-w-[120px]" title={waitingFor}>
          {waitingFor}
        </span>
      </span>
    </button>
  )
}

// ── Selected-log view ────────────────────────────────────────────────────────

interface SelectedLogViewProps {
  selectedLog: RunLog | null
  nodeInfoById: Map<string, NodeInfo>
  tab: Tab
  setTab: (t: Tab) => void
  payload: unknown
}

function SelectedLogView({
  selectedLog, nodeInfoById, tab, setTab, payload,
}: SelectedLogViewProps) {
  if (!selectedLog) {
    return (
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex shrink-0 items-center gap-1 border-b border-[var(--border-faint)] px-3 py-1.5">
          <span className="px-1 text-[11.5px] text-[var(--text-faint)]">
            Select a node to view its details.
          </span>
        </div>
      </div>
    )
  }

  const info: NodeInfo = (selectedLog.nodeId && nodeInfoById.get(selectedLog.nodeId)) || {
    label: selectedLog.message || selectedLog.nodeId || 'Log',
    icon: 'Box',
  }
  const payloadObj = selectedLog.payload as Record<string, unknown> | null | undefined
  const errored = !!payloadObj && 'error' in payloadObj
  const waitingPayload = payloadObj?.waiting as
    | { waitingFor: string; targetId?: string | null; ttlSeconds?: number | null; startedAt?: string | null }
    | undefined

  if (waitingPayload) {
    return <WaitingView nodeInfo={info} payload={waitingPayload} />
  }

  if (errored && tab === 'output' && selectedLog.nodeId) {
    return (
      <div className="flex min-w-0 flex-1 flex-col">
        <ErrorView log={selectedLog} nodeInfo={info} tab={tab} onTabChange={setTab} />
      </div>
    )
  }

  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <JsonInspector
        payload={payload}
        nodeId={selectedLog.nodeId}
        nodeLabel={info.label}
        tab={tab}
        onTabChange={setTab}
        downloadName={`${selectedLog.nodeId || 'log'}-${tab}`}
      />
    </div>
  )
}
