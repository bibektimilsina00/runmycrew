import { useEffect, useRef } from 'react'
import { useAuthStore } from '@/features/auth/store/authStore'
import {
  useRunsStore,
  normalizeLevel,
  type AgentTraceStep,
  type RunLog,
} from '../store/runsStore'
import { apiWsBaseUrl } from '../utils/wsUrl'

// React StrictMode runs effect mount → cleanup → mount in dev, which
// would otherwise spawn two WebSockets for the same execution. The
// backend handles a vanished client cleanly now, but the duplicate
// socket still costs a connect/subscribe round-trip and shows up as
// two open lines in the run timeline. We defer cleanup-driven close
// by a tick — if the same effect re-mounts (StrictMode), it cancels
// the pending close and reuses the same socket. Real unmounts still
// close (after the short delay).
const STRICTMODE_REUSE_WINDOW_MS = 150

/**
 * Subscribe to /ws/executions/{id}. Streams catch-up + live `log_synced` events
 * and terminal `execution_completed | execution_failed` into the workflow's
 * runs slice. Server closes the socket on terminal status — no reconnect.
 */
export function useRunStream(workflowId: string | null, executionId: string | null): void {
  const appendLog = useRunsStore((s) => s.appendLog)
  const setStatus = useRunsStore((s) => s.setStatus)
  const startRun = useRunsStore((s) => s.startRun)
  const setNodeStatus = useRunsStore((s) => s.setNodeStatus)
  const setWaiting = useRunsStore((s) => s.setWaiting)
  const appendAgentTrace = useRunsStore((s) => s.appendAgentTrace)

  // Persisted across StrictMode mount-cleanup-mount cycles for the
  // same component instance. Carries the live socket + a pending-close
  // timer so the second mount can cancel the timer and reuse the
  // socket instead of opening a new one.
  const socketRef = useRef<{
    ws: WebSocket
    executionId: string
    closeTimer: ReturnType<typeof setTimeout> | null
  } | null>(null)

  useEffect(() => {
    if (!workflowId || !executionId) return
    // Synthetic ids minted by recordRunFailure() never had a server-side
    // execution row, so opening a WS to them would 404 in a loop.
    if (executionId.startsWith('local-fail-')) return

    const token =
      useAuthStore.getState().token || localStorage.getItem('runmycrew-auth-token') || ''
    if (!token) return

    startRun(workflowId, executionId)

    // Reuse the socket from a just-cancelled cleanup if it's still open
    // for the same execution. StrictMode mount → cleanup → mount lands
    // inside the reuse window, so we skip the new-WebSocket round-trip
    // entirely.
    const existing = socketRef.current
    if (
      existing &&
      existing.executionId === executionId &&
      existing.ws.readyState === WebSocket.OPEN
    ) {
      if (existing.closeTimer) {
        clearTimeout(existing.closeTimer)
        existing.closeTimer = null
      }
      return () => {
        if (socketRef.current) {
          socketRef.current.closeTimer = setTimeout(() => {
            socketRef.current?.ws.close()
            socketRef.current = null
          }, STRICTMODE_REUSE_WINDOW_MS)
        }
      }
    }

    // Different execution or no live socket — close any prior one and
    // open a fresh connection.
    if (existing) {
      if (existing.closeTimer) clearTimeout(existing.closeTimer)
      existing.ws.close()
      socketRef.current = null
    }

    const url = `${apiWsBaseUrl()}/ws/executions/${executionId}?token=${encodeURIComponent(token)}`
    const ws: WebSocket = new WebSocket(url)
    socketRef.current = { ws, executionId, closeTimer: null }
    let alive = true
    let liveCounter = 0

    ws.onmessage = (ev) => {
      if (ev.data === 'ping' || ev.data === 'pong') return
      let data: Record<string, unknown>
      try {
        data = JSON.parse(ev.data)
      } catch {
        return
      }
      const type = String(data.type ?? '')

      if (type === 'log_synced') {
        // Catch-up shape: {id, timestamp, node_id, level, message, payload}
        // Live shape:     {node_id, lvl, src, msg, payload, t} — no id, drift in field names
        const log: RunLog = {
          id: typeof data.id === 'string' ? data.id : `live-${executionId}-${++liveCounter}`,
          nodeId: typeof data.node_id === 'string' ? data.node_id : null,
          level: normalizeLevel(data.level ?? data.lvl),
          message: String(data.message ?? data.msg ?? ''),
          payload: (data.payload as Record<string, unknown> | null) ?? null,
          timestamp: String(data.timestamp ?? data.t ?? new Date().toISOString()),
        }
        appendLog(workflowId, executionId, log)
      } else if (type === 'tool_call_started' || type === 'tool_call_completed') {
        // Agent tool-call timeline (PR7). Dual-write:
        //  1. A synthetic RunLog so the runs list keeps the inline event.
        //  2. A structured `AgentTraceStep` so the dedicated Trace tab
        //     can render a live stepper with args/result/duration.
        const toolId = String(data.tool_id ?? 'tool')
        const args = (data.arguments as Record<string, unknown> | null) ?? null
        const started = type === 'tool_call_started'
        const success = data.success === true
        const durationMs = typeof data.duration_ms === 'number' ? data.duration_ms : null
        const result = (data.result as Record<string, unknown> | null) ?? null
        const nodeId = typeof data.node_id === 'string' ? data.node_id : null
        const iteration = typeof data.iteration === 'number' ? data.iteration : 0
        appendLog(workflowId, executionId, {
          id: `live-${executionId}-${++liveCounter}`,
          nodeId,
          level: started ? 'info' : success ? 'info' : 'error',
          message: started
            ? `▶ ${toolId} running`
            : success
              ? `✓ ${toolId}${durationMs !== null ? ` · ${durationMs}ms` : ''}`
              : `✗ ${toolId}${durationMs !== null ? ` · ${durationMs}ms` : ''}`,
          payload: started ? { arguments: args } : { result, duration_ms: durationMs },
          timestamp: new Date().toISOString(),
        })

        // Stable step id = nodeId|iteration|toolId|argsKey. The completed
        // event re-derives the same id so we update in place rather than
        // appending a second step.
        if (nodeId) {
          const argsKey = args ? JSON.stringify(args) : ''
          const stepId = `${nodeId}|${iteration}|${toolId}|${argsKey}`
          const now = new Date().toISOString()
          const step: AgentTraceStep = started
            ? {
                id: stepId,
                nodeId,
                iteration,
                toolId,
                status: 'running',
                startedAt: now,
                endedAt: null,
                durationMs: null,
                arguments: args,
                result: null,
                errorMessage: null,
              }
            : {
                id: stepId,
                nodeId,
                iteration,
                toolId,
                status: success ? 'success' : 'failed',
                startedAt: now,
                endedAt: now,
                durationMs,
                arguments: args,
                result,
                errorMessage:
                  !success && result && typeof result.error === 'string'
                    ? (result.error as string)
                    : null,
              }
          appendAgentTrace(workflowId, executionId, step)
        }
      } else if (type === 'node_started' || type === 'node_completed' || type === 'node_failed') {
        // Per-node lifecycle stream. Drives canvas status indicators
        // independent of whether the node also emits logs — triggers and
        // instant-finish nodes still get a visible state transition.
        const nodeId = typeof data.node_id === 'string' ? data.node_id : null
        if (nodeId) {
          const next =
            type === 'node_started'
              ? 'running'
              : type === 'node_completed'
                ? 'completed'
                : 'failed'
          setNodeStatus(workflowId, executionId, nodeId, next)
        }
      } else if (type === 'execution_waiting') {
        const waitingFor =
          typeof data.waiting_for === 'string' ? data.waiting_for : null
        setWaiting(workflowId, executionId, waitingFor)
      } else if (type === 'execution_cancelled') {
        setStatus(workflowId, executionId, 'cancelled')
      } else if (type === 'execution_timeout') {
        // Polling-trigger listen window expired with no event. Treat as
        // a benign terminal state — the user is told to retry; we don't
        // want it to surface as a red "failed" run.
        setStatus(workflowId, executionId, 'cancelled')
      } else if (type === 'execution_listen_matched') {
        // Pure progress event from the polling listener — keep status
        // as `waiting` until `execution_started` arrives so the canvas
        // doesn't blink between the two transitions.
      } else if (type === 'execution_started') {
        // Listen slot fired — flip out of `waiting` so the canvas
        // unfreezes the "Waiting…" badge. node_started events follow.
        setStatus(workflowId, executionId, 'running')
      } else if (type === 'execution_completed' || type === 'execution_failed') {
        // Terminal events carry the final per-node lifecycle for sockets
        // that attached mid-run and missed the individual node_* frames.
        const finalStatuses = data.node_statuses
        if (finalStatuses && typeof finalStatuses === 'object') {
          for (const [nid, st] of Object.entries(finalStatuses as Record<string, string>)) {
            if (st === 'completed' || st === 'failed' || st === 'running') {
              setNodeStatus(workflowId, executionId, nid, st)
            }
          }
        }
        setStatus(workflowId, executionId, type === 'execution_completed' ? 'completed' : 'failed')
      }
    }

    ws.onclose = () => {
      if (!alive) return
      // Server closes on terminal status; if no terminal event arrived, leave
      // status as-is (it may have streamed during the session).
      if (socketRef.current?.ws === ws) socketRef.current = null
    }

    return () => {
      alive = false
      // Defer the close so a StrictMode re-mount can reclaim the socket.
      // A real unmount (or executionId change) hits the timer and closes
      // for real.
      if (socketRef.current?.ws === ws) {
        socketRef.current.closeTimer = setTimeout(() => {
          ws.close()
          if (socketRef.current?.ws === ws) socketRef.current = null
        }, STRICTMODE_REUSE_WINDOW_MS)
      } else {
        ws.close()
      }
    }
  }, [
    workflowId,
    executionId,
    appendLog,
    setStatus,
    startRun,
    setNodeStatus,
    setWaiting,
    appendAgentTrace,
  ])
}
