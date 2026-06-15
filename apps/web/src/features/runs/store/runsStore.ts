import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface RunLog {
  id: string
  nodeId: string | null
  level: 'info' | 'warn' | 'error'
  message: string
  payload: Record<string, unknown> | null
  timestamp: string
}

export type RunStatus =
  | 'pending'
  | 'waiting'   // Listen-for-test-event mode — slot open, no webhook yet
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'

/** Per-node lifecycle status, fed by `node_started` / `node_completed` /
 *  `node_failed` events streamed from the execution engine. Keyed by node
 *  id within a run. Decouples canvas indicators from log-scan heuristics
 *  so triggers + nodes that emit no logs still surface a running state. */
export type NodeRunStatus = 'running' | 'completed' | 'failed'

export interface Run {
  executionId: string
  status: RunStatus
  logs: RunLog[]
  nodeStatuses: Record<string, NodeRunStatus>
  /** Human label shown while a listen slot waits for the next event. */
  waitingFor?: string | null
  /** Trigger node holding the listen slot — surfaced as the "waiting" row
   * in the runs list so the user sees *which* node is listening. */
  listenNodeId?: string | null
  /** Resource the slot is bound to (Page id / IG user id / WABA id). */
  listenTargetId?: string | null
  /** Slot TTL in seconds at open time — fed into the countdown UI. */
  listenTtlSeconds?: number | null
  /** ISO timestamp when the slot was opened (countdown reference). */
  listenStartedAt?: string | null
}

export interface WorkflowRunsSlice {
  runs: Run[]
  activeExecutionId: string | null
  selectedLogId: string | null
}

interface RunsState {
  byWorkflow: Record<string, WorkflowRunsSlice>
  setActiveExecutionId: (workflowId: string, executionId: string | null) => void
  startRun: (workflowId: string, executionId: string) => void
  appendLog: (workflowId: string, executionId: string, log: RunLog) => void
  setStatus: (workflowId: string, executionId: string, status: RunStatus) => void
  setNodeStatus: (
    workflowId: string,
    executionId: string,
    nodeId: string,
    status: NodeRunStatus,
  ) => void
  setWaiting: (
    workflowId: string,
    executionId: string,
    waitingFor: string | null,
  ) => void
  startListen: (
    workflowId: string,
    executionId: string,
    waitingFor: string,
    detail?: {
      nodeId?: string
      targetId?: string
      ttlSeconds?: number
      startedAt?: string
    },
  ) => void
  recordRunFailure: (
    workflowId: string,
    message: string,
    nodeId: string,
  ) => string
  setSelectedLogId: (workflowId: string, id: string | null) => void
  clearRuns: (workflowId: string) => void
}

export const EMPTY_SLICE: WorkflowRunsSlice = Object.freeze({
  runs: [],
  activeExecutionId: null,
  selectedLogId: null,
})

const LEVEL_MAP: Record<string, RunLog['level']> = {
  info: 'info',
  warning: 'warn',
  warn: 'warn',
  error: 'error',
  err: 'error',
}

export function normalizeLevel(raw: unknown): RunLog['level'] {
  return LEVEL_MAP[String(raw)] ?? 'info'
}

function readSlice(
  byWorkflow: Record<string, WorkflowRunsSlice>,
  workflowId: string,
): WorkflowRunsSlice {
  return byWorkflow[workflowId] ?? { runs: [], activeExecutionId: null, selectedLogId: null }
}

function withSlice(
  state: { byWorkflow: Record<string, WorkflowRunsSlice> },
  workflowId: string,
  updater: (slice: WorkflowRunsSlice) => WorkflowRunsSlice,
): { byWorkflow: Record<string, WorkflowRunsSlice> } | object {
  const current = readSlice(state.byWorkflow, workflowId)
  const next = updater(current)
  if (next === current) return {}
  return { byWorkflow: { ...state.byWorkflow, [workflowId]: next } }
}

const MAX_RUNS_PER_WORKFLOW = 20

export const useRunsStore = create<RunsState>()(
  persist(
    (set) => ({
  byWorkflow: {},

  setActiveExecutionId: (workflowId, activeExecutionId) =>
    set((s) => withSlice(s, workflowId, (slice) => ({ ...slice, activeExecutionId }))),

  startRun: (workflowId, executionId) =>
    set((s) =>
      withSlice(s, workflowId, (slice) => {
        if (slice.runs.some((r) => r.executionId === executionId)) return slice
        return {
          ...slice,
          runs: [
            ...slice.runs,
            { executionId, status: 'running', logs: [], nodeStatuses: {} },
          ],
        }
      }),
    ),

  appendLog: (workflowId, executionId, log) =>
    set((s) =>
      withSlice(s, workflowId, (slice) => {
        const runs = slice.runs.map((r) => {
          if (r.executionId !== executionId) return r
          if (r.logs.some((l) => l.id === log.id)) return r
          // Content fallback — guards against catch-up replays sending the
          // same log under a different id (synthetic `live-*` vs DB UUID).
          // Timestamp is intentionally excluded: live and catch-up paths can
          // serialize the same instant slightly differently.
          const payloadKey = log.payload ? Object.keys(log.payload).sort().join(',') : ''
          const key = `${log.nodeId ?? ''}|${log.level}|${log.message}|${payloadKey}`
          if (
            r.logs.some(
              (l) =>
                `${l.nodeId ?? ''}|${l.level}|${l.message}|${l.payload ? Object.keys(l.payload).sort().join(',') : ''}` ===
                key,
            )
          ) {
            return r
          }
          return { ...r, logs: [...r.logs, log] }
        })
        // Auto-select the first node log so the inspector isn't empty.
        const selectedLogId = slice.selectedLogId ?? (log.nodeId ? log.id : null)
        return { ...slice, runs, selectedLogId }
      }),
    ),

  setStatus: (workflowId, executionId, status) =>
    set((s) =>
      withSlice(s, workflowId, (slice) => ({
        ...slice,
        runs: slice.runs.map((r) => (r.executionId === executionId ? { ...r, status } : r)),
      })),
    ),

  setNodeStatus: (workflowId, executionId, nodeId, status) =>
    set((s) =>
      withSlice(s, workflowId, (slice) => ({
        ...slice,
        runs: slice.runs.map((r) => {
          if (r.executionId !== executionId) return r
          // `running` never overwrites a terminal state — late `node_started`
          // events arriving after `node_completed` (out-of-order delivery)
          // would otherwise blink the indicator back to running.
          if (status === 'running' && (r.nodeStatuses[nodeId] === 'completed' || r.nodeStatuses[nodeId] === 'failed')) {
            return r
          }
          return {
            ...r,
            nodeStatuses: { ...r.nodeStatuses, [nodeId]: status },
          }
        }),
      })),
    ),

  setWaiting: (workflowId, executionId, waitingFor) =>
    set((s) =>
      withSlice(s, workflowId, (slice) => ({
        ...slice,
        runs: slice.runs.map((r) =>
          r.executionId === executionId
            ? { ...r, status: 'waiting' as const, waitingFor }
            : r,
        ),
      })),
    ),

  startListen: (workflowId, executionId, waitingFor, detail) =>
    set((s) =>
      withSlice(s, workflowId, (slice) => {
        const listenFields = {
          listenNodeId: detail?.nodeId ?? null,
          listenTargetId: detail?.targetId ?? null,
          listenTtlSeconds: detail?.ttlSeconds ?? null,
          listenStartedAt: detail?.startedAt ?? new Date().toISOString(),
        }
        if (slice.runs.some((r) => r.executionId === executionId)) {
          return {
            ...slice,
            activeExecutionId: executionId,
            runs: slice.runs.map((r) =>
              r.executionId === executionId
                ? { ...r, status: 'waiting' as const, waitingFor, ...listenFields }
                : r,
            ),
          }
        }
        return {
          ...slice,
          activeExecutionId: executionId,
          // Pre-select the waiting row so the right pane opens straight to
          // WaitingView without an extra click.
          selectedLogId: detail?.nodeId ? `${executionId}-waiting` : slice.selectedLogId,
          runs: [
            ...slice.runs,
            {
              executionId,
              status: 'waiting' as const,
              logs: [],
              nodeStatuses: {},
              waitingFor,
              ...listenFields,
            },
          ],
        }
      }),
    ),

  recordRunFailure: (workflowId, message, nodeId) => {
    // Synthetic execution id — no row exists on the server because the
    // request never made it past the listen/run handler. Prefixed so it
    // can't collide with real UUIDs and so the WS hook can ignore it.
    // The log is shaped like a real node-failure log (nodeId + payload.error)
    // so it lights up LogsPanel's per-node row and ErrorView on the right.
    const executionId = `local-fail-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    const logId = `${executionId}-log`
    set((s) =>
      withSlice(s, workflowId, (slice) => ({
        ...slice,
        activeExecutionId: executionId,
        selectedLogId: logId,
        runs: [
          ...slice.runs,
          {
            executionId,
            status: 'failed' as const,
            logs: [
              {
                id: logId,
                nodeId,
                level: 'error' as const,
                message,
                payload: { error: message },
                timestamp: new Date().toISOString(),
              },
            ],
            nodeStatuses: { [nodeId]: 'failed' as const },
          },
        ],
      })),
    )
    return executionId
  },

  setSelectedLogId: (workflowId, selectedLogId) =>
    set((s) => withSlice(s, workflowId, (slice) => ({ ...slice, selectedLogId }))),

  clearRuns: (workflowId) =>
    set((s) =>
      withSlice(s, workflowId, () => ({
        runs: [],
        activeExecutionId: null,
        selectedLogId: null,
      })),
    ),
}),
    {
      name: 'fuse-runs',
      version: 3,
      partialize: (s) => ({ byWorkflow: s.byWorkflow }),
      merge: (persisted, current) => {
        const p = (persisted ?? {}) as Partial<RunsState>
        const trimmed: Record<string, WorkflowRunsSlice> = {}
        for (const [wfId, slice] of Object.entries(p.byWorkflow ?? {})) {
          // Cap log history to the last MAX_RUNS_PER_WORKFLOW runs to keep
          // localStorage from growing unbounded across long-lived sessions.
          // Backfill `nodeStatuses` on runs persisted under v2 so selectors
          // don't crash on `r.nodeStatuses[nodeId]` for older entries.
          const runs = slice.runs.slice(-MAX_RUNS_PER_WORKFLOW).map((r) => ({
            ...r,
            nodeStatuses: r.nodeStatuses ?? {},
          }))
          trimmed[wfId] = { ...slice, runs }
        }
        return { ...current, ...p, byWorkflow: trimmed }
      },
    },
  ),
)

/**
 * Read a workflow's runs slice. Returns the frozen empty slice when the
 * workflow has no recorded runs yet — same reference on every miss, so the
 * selector does not trigger re-renders.
 */
export function useWorkflowRuns(workflowId: string | null): WorkflowRunsSlice {
  return useRunsStore((s) => (workflowId ? s.byWorkflow[workflowId] ?? EMPTY_SLICE : EMPTY_SLICE))
}

/**
 * Latest run for a workflow — used by node border styling.
 */
export function useLatestRunForWorkflow(workflowId: string | null): Run | null {
  return useRunsStore((s) => {
    if (!workflowId) return null
    const slice = s.byWorkflow[workflowId]
    if (!slice || !slice.runs.length) return null
    return slice.runs[slice.runs.length - 1]
  })
}
