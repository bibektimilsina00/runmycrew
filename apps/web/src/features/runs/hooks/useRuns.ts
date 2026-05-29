import { useState, useEffect, useRef } from 'react'
import type { Run, RunStatus } from '@/features/runs/types/runsTypes'
import { runsAPI, type ApiExecution } from '@/features/runs/services/runsAPI'
import { useAuthStore } from '@/features/auth/store/authStore'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { logger } from '@/shared/utils/logger'

export function mapBackendRun(r: ApiExecution): Run {
  let status: RunStatus = 'ok'
  if (r.status === 'completed') status = 'ok'
  else if (r.status === 'failed' || r.status === 'cancelled') status = 'err'
  else if (r.status === 'paused') status = 'warn'
  else if (r.status === 'running' || r.status === 'pending' || r.status === 'cancelling') status = 'run'

  const trigger = r.trigger_type || 'manual'

  let duration = 'running…'
  if (r.duration_ms !== null && r.duration_ms !== undefined) {
    duration = `${(r.duration_ms / 1000).toFixed(1)}s`
  } else if (r.status === 'completed' || r.status === 'failed' || r.status === 'cancelled') {
    if (r.started_at && r.finished_at) {
      const d = new Date(r.finished_at).getTime() - new Date(r.started_at).getTime()
      duration = `${(d / 1000).toFixed(1)}s`
    } else {
      duration = '0.0s'
    }
  }

  let started = ''
  if (r.started_at) {
    try {
      const date = new Date(r.started_at)
      if (!isNaN(date.getTime())) {
        const pad = (n: number) => String(n).padStart(2, '0')
        started = `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
      }
    } catch {
      started = r.started_at
    }
  }

  return {
    id: r.id,
    status,
    name: r.workflow_name || 'Unnamed workflow',
    trigger,
    started,
    duration,
    startedAt: r.started_at || new Date().toISOString(),
  }
}

export function useRuns() {
  const [items, setItems] = useState<Run[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const isPausedRef = useRef(isPaused)
  const bufferRef = useRef<Run[]>([])

  useEffect(() => {
    isPausedRef.current = isPaused
  }, [isPaused])

  const workspaceId = useWorkspaceStore((state) => state.currentWorkspaceId)
  const token = useAuthStore((state) => state.token)

  // Apply buffered runs when resuming the stream
  useEffect(() => {
    if (!isPaused && bufferRef.current.length > 0) {
      setItems((prev) => {
        let updated = [...prev]
        for (const bufferedRun of bufferRef.current) {
          const idx = updated.findIndex((item) => item.id === bufferedRun.id)
          if (idx > -1) {
            updated[idx] = bufferedRun
          } else {
            updated = [bufferedRun, ...updated]
          }
        }
        bufferRef.current = []
        return updated
      })
    }
  }, [isPaused])

  // 1. Fetch initial runs when workspaceId changes
  useEffect(() => {
    if (!workspaceId) return

    const controller = new AbortController()

    runsAPI.getAll(controller.signal)
      .then((data) => {
        setItems(data.executions.map(mapBackendRun))
      })
      .catch((err) => {
        if (err.name !== 'CanceledError') {
          logger.error('Failed to load initial runs', err)
        }
      })

    return () => {
      controller.abort()
    }
  }, [workspaceId])

  // 2. Connect WebSocket stream for real-time runs updates
  useEffect(() => {
    if (!workspaceId) return

    const resolvedToken = token || localStorage.getItem('fuse-auth-token') || ''
    if (!resolvedToken) return

    const rawApiUrl = import.meta.env.VITE_API_URL || '/api/v1'
    const wsBaseUrl = rawApiUrl.startsWith('http://') || rawApiUrl.startsWith('https://')
      ? rawApiUrl.replace(/^http/, 'ws')
      : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host}${rawApiUrl}`

    const wsUrl = `${wsBaseUrl}/ws/workspaces/${workspaceId}/runs?token=${encodeURIComponent(resolvedToken)}`

    let ws: WebSocket | null = null
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null
    let shouldReconnect = true

    function connect() {
      if (!shouldReconnect) return

      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        logger.info('[WorkspaceRunsWS] Connected')
      }

      ws.onmessage = (event) => {
        try {
          if (event.data === 'ping' || event.data === 'pong') return
          const data = JSON.parse(event.data)
          if (data.type === 'run_updated' && data.run) {
            const updatedRun = mapBackendRun(data.run)
            if (isPausedRef.current) {
              const idx = bufferRef.current.findIndex(r => r.id === updatedRun.id)
              if (idx > -1) {
                bufferRef.current[idx] = updatedRun
              } else {
                bufferRef.current.push(updatedRun)
              }
            } else {
              setItems((prev) => {
                const idx = prev.findIndex((item) => item.id === updatedRun.id)
                if (idx > -1) {
                  const updated = [...prev]
                  updated[idx] = updatedRun
                  return updated
                } else {
                  return [updatedRun, ...prev]
                }
              })
            }
          }
        } catch (err) {
          logger.warn('[WorkspaceRunsWS] Failed to parse message', err)
        }
      }

      ws.onclose = () => {
        logger.info('[WorkspaceRunsWS] Disconnected')
        if (shouldReconnect) {
          reconnectTimeout = setTimeout(connect, 3000)
        }
      }

      ws.onerror = (err) => {
        logger.error('[WorkspaceRunsWS] Error', err)
      }
    }

    connect()

    return () => {
      shouldReconnect = false
      if (ws) {
        ws.close()
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
      }
    }
  }, [workspaceId, token])

  return {
    items,
    isPaused,
    setIsPaused,
  }
}
