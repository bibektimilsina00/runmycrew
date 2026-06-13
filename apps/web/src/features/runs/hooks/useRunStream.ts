import { useEffect } from 'react'
import { useAuthStore } from '@/features/auth/store/authStore'
import { useRunsStore, normalizeLevel, type RunLog } from '../store/runsStore'

function buildWsUrl(): string {
  const rawApiUrl = import.meta.env.VITE_API_URL || '/api/v1'
  if (rawApiUrl.startsWith('http://') || rawApiUrl.startsWith('https://')) {
    return rawApiUrl.replace(/^http/, 'ws')
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host =
    window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host
  return `${proto}//${host}${rawApiUrl}`
}

/**
 * Subscribe to /ws/executions/{id}. Streams catch-up + live `log_synced` events
 * and terminal `execution_completed | execution_failed` into the workflow's
 * runs slice. Server closes the socket on terminal status — no reconnect.
 */
export function useRunStream(workflowId: string | null, executionId: string | null): void {
  const appendLog = useRunsStore((s) => s.appendLog)
  const setStatus = useRunsStore((s) => s.setStatus)
  const startRun = useRunsStore((s) => s.startRun)

  useEffect(() => {
    if (!workflowId || !executionId) return

    const token =
      useAuthStore.getState().token || localStorage.getItem('fuse-auth-token') || ''
    if (!token) return

    startRun(workflowId, executionId)

    const url = `${buildWsUrl()}/ws/executions/${executionId}?token=${encodeURIComponent(token)}`
    let ws: WebSocket | null = new WebSocket(url)
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
        // Agent tool-call timeline (PR7). Surfaced as synthetic RunLog
        // entries scoped to the agent's node id so they appear inline
        // with the rest of that node's logs.
        const toolId = String(data.tool_id ?? 'tool')
        const args = (data.arguments as Record<string, unknown> | null) ?? null
        const started = type === 'tool_call_started'
        const success = data.success === true
        const durationMs = typeof data.duration_ms === 'number' ? data.duration_ms : null
        const result = (data.result as Record<string, unknown> | null) ?? null
        appendLog(workflowId, executionId, {
          id: `live-${executionId}-${++liveCounter}`,
          nodeId: typeof data.node_id === 'string' ? data.node_id : null,
          level: started ? 'info' : success ? 'info' : 'error',
          message: started
            ? `▶ ${toolId} running`
            : success
              ? `✓ ${toolId}${durationMs !== null ? ` · ${durationMs}ms` : ''}`
              : `✗ ${toolId}${durationMs !== null ? ` · ${durationMs}ms` : ''}`,
          payload: started ? { arguments: args } : { result, duration_ms: durationMs },
          timestamp: new Date().toISOString(),
        })
      } else if (type === 'execution_completed' || type === 'execution_failed') {
        setStatus(workflowId, executionId, type === 'execution_completed' ? 'completed' : 'failed')
      }
    }

    ws.onclose = () => {
      if (!alive) return
      // Server closes on terminal status; if no terminal event arrived, leave
      // status as-is (it may have streamed during the session).
    }

    return () => {
      alive = false
      ws?.close()
      ws = null
    }
  }, [workflowId, executionId, appendLog, setStatus, startRun])
}
