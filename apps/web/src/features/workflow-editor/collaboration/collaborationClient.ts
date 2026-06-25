import type { ClientEvent, ServerEvent } from './types'

/**
 * Thin WebSocket wrapper for the workflow collaboration channel.
 *
 * - Sends a heartbeat every 30s so the server's 60s receive timeout
 *   doesn't tear the connection down on an idle tab.
 * - Reconnects with exponential backoff (capped) on transport errors.
 * - Buffers nothing — if a send happens while disconnected we drop it
 *   on the floor. Cursor / selection events are continuous anyway, so
 *   one lost packet is invisible; graph.saved is a notification, not
 *   the source of truth (DB persistence is separate).
 */

const HEARTBEAT_MS = 30_000
const INITIAL_RECONNECT_MS = 1_000
const MAX_RECONNECT_MS = 15_000

interface ClientOptions {
  workflowId: string
  workspaceId: string
  token: string
  onEvent: (event: ServerEvent) => void
  onOpen?: () => void
  onClose?: (code: number) => void
}

function buildWsUrl({
  workflowId,
  workspaceId,
  token,
}: {
  workflowId: string
  workspaceId: string
  token: string
}): string {
  // Backend mounts the websocket at /api/v1/ws/workflows/:id/collaboration
  // (apps/api/app/api/v1/router.py:47). The HTTP base lives in
  // VITE_API_URL; we swap http→ws / https→wss and append the path.
  const apiBase = import.meta.env.VITE_API_URL || `${window.location.origin}/api/v1`
  const httpUrl = apiBase.startsWith('http')
    ? apiBase
    : `${window.location.origin}${apiBase}`
  const wsBase = httpUrl.replace(/^http/, 'ws')
  const params = new URLSearchParams({ token, workspace_id: workspaceId })
  return `${wsBase}/ws/workflows/${workflowId}/collaboration?${params.toString()}`
}

export class CollaborationClient {
  private socket: WebSocket | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectDelayMs = INITIAL_RECONNECT_MS
  private closedByCaller = false
  private readonly opts: ClientOptions

  constructor(opts: ClientOptions) {
    this.opts = opts
  }

  connect(): void {
    this.closedByCaller = false
    this.openSocket()
  }

  disconnect(): void {
    this.closedByCaller = true
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.reconnectTimer = null
    this.stopHeartbeat()
    if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
      // 1000 is the "normal closure" code — the server uses it for the
      // graceful path so passing it back lets backend logs distinguish
      // tab-close from network drops.
      this.socket.close(1000)
    }
    this.socket = null
  }

  send(event: ClientEvent): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return
    this.socket.send(JSON.stringify(event))
  }

  private openSocket(): void {
    const url = buildWsUrl(this.opts)
    const socket = new WebSocket(url)
    this.socket = socket

    socket.onopen = () => {
      this.reconnectDelayMs = INITIAL_RECONNECT_MS
      this.startHeartbeat()
      this.opts.onOpen?.()
    }

    socket.onmessage = (msg) => {
      try {
        const parsed = JSON.parse(msg.data) as ServerEvent
        this.opts.onEvent(parsed)
      } catch {
        // Ignore malformed payloads — backend should never send any,
        // and a parse failure shouldn't tear the connection down.
      }
    }

    socket.onclose = (ev) => {
      this.stopHeartbeat()
      this.opts.onClose?.(ev.code)
      // 4001 is the server's "auth failed" code — no point reconnecting
      // because the token won't fix itself. Anything else gets a retry.
      if (this.closedByCaller || ev.code === 4001) return
      this.scheduleReconnect()
    }

    socket.onerror = () => {
      // onerror is followed by onclose; reconnect logic lives there to
      // avoid double-scheduling.
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      this.send({ type: 'heartbeat' })
    }, HEARTBEAT_MS)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer)
    this.heartbeatTimer = null
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelayMs = Math.min(this.reconnectDelayMs * 2, MAX_RECONNECT_MS)
      this.openSocket()
    }, this.reconnectDelayMs)
  }
}
