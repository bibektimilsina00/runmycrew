import { useCallback, useEffect, useMemo, useRef } from 'react'
import type { Node } from 'reactflow'
import { useAuthStore } from '@/stores/auth-store'
import { useCollaborationStore } from '@/stores/collaboration-store'
import { useWorkflowStore, type GraphPatch } from '@/stores/workflow-store'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { logger } from '@/lib/logger'

interface CollaborationSession {
  session_id: string
  user_id: string
  user_name: string
  avatar_url: string | null
  color: string
  connected_at: string  // always set by server
}

interface CollaborationEvent {
  type: string
  session?: CollaborationSession
  sessions?: CollaborationSession[]
  payload?: Record<string, unknown>
  patch_id?: string
}

function websocketUrl(workflowId: string, token: string, workspaceId: string) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const baseUrl = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host
  const params = new URLSearchParams({ token, workspace_id: workspaceId })
  return `${protocol}//${baseUrl}/api/v1/ws/workflows/${workflowId}/collaboration?${params.toString()}`
}

export function useWorkflowCollaboration(workflowId: string | null) {
  const token = useAuthStore(s => s.token)
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  const applyRemoteGraphPatch = useWorkflowStore(s => s.applyRemoteGraphPatch)
  const setWsStatus = useCollaborationStore(s => s.setWsStatus)
  const resetCollaboration = useCollaborationStore(s => s.reset)
  const setMySessionId = useCollaborationStore(s => s.setMySessionId)
  const setPresence = useCollaborationStore(s => s.setPresence)
  const removePresence = useCollaborationStore(s => s.removePresence)
  const updateCursor = useCollaborationStore(s => s.updateCursor)
  const setNodeSelection = useCollaborationStore(s => s.setNodeSelection)
  const setMyUserId = useCollaborationStore(s => s.setMyUserId)
  const wsRef = useRef<WebSocket | null>(null)
  const heartbeatRef = useRef<number>(0)

  useEffect(() => {
    if (!workflowId || !token || !workspaceId) return
    setWsStatus('connecting')
    const ws = new WebSocket(websocketUrl(workflowId, token, workspaceId))
    wsRef.current = ws

    ws.onopen = () => {
      setWsStatus('connected')
      // Send heartbeat every 30s to keep presence alive (TTL is 90s)
      heartbeatRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'heartbeat', payload: {} }))
        }
      }, 30_000)
    }
    ws.onclose = () => {
      setWsStatus('disconnected')
      resetCollaboration()
      clearInterval(heartbeatRef.current)
    }
    ws.onerror = event => logger.error('[Collaboration] WebSocket error', event)
    ws.onmessage = event => {
      let message: CollaborationEvent
      try {
        message = JSON.parse(event.data) as CollaborationEvent
      } catch (err) {
        logger.error('[Collaboration] Failed to parse message', err)
        return
      }
      if (message.type === 'session.ready' && message.session) {
        setMySessionId(message.session.session_id)
        setMyUserId(message.session.user_id)  // track user_id to filter ALL own sessions
        return
      }
      if (message.type === 'presence.snapshot') {
        message.sessions?.forEach(session => setPresence(toPresence(session)))
        return
      }
      if (message.type === 'presence.joined' && message.session) setPresence(toPresence(message.session))
      if (message.type === 'presence.left' && message.session) removePresence(message.session.session_id)
      if (message.type === 'cursor.moved' && message.session) {
        const cursor = message.payload?.cursor
        if (isCursor(cursor)) updateCursor(message.session.session_id, cursor)
      }
      if (message.type === 'selection.changed' && message.session) {
        const nodeId = typeof message.payload?.nodeId === 'string' ? message.payload.nodeId : null
        setNodeSelection(message.session.session_id, nodeId)
      }
      if (message.type === 'graph.patch') {
        const patch = message.payload?.patch
        if (isGraphPatch(patch)) applyRemoteGraphPatch(patch)
      }
      if (message.type === 'graph.saved') {
        const version = message.payload?.version
        if (typeof version === 'number') useWorkflowStore.getState().markSaved(version)
      }
    }

    return () => {
      clearInterval(heartbeatRef.current)
      ws.close()
      wsRef.current = null
    }
  }, [
    workflowId,
    token,
    workspaceId,
    applyRemoteGraphPatch,
    setWsStatus,
    resetCollaboration,
    setMySessionId,
    setMyUserId,
    setPresence,
    removePresence,
    updateCursor,
    setNodeSelection,
  ])

  const send = useCallback((type: string, payload: Record<string, unknown>, patchId?: string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return
    wsRef.current.send(JSON.stringify({ type, payload, patch_id: patchId }))
  }, [])

  const sendCursor = useCallback((cursor: { x: number; y: number; viewport: { x: number; y: number; zoom: number } }) => {
    send('cursor.moved', { cursor })
  }, [send])

  const sendSelection = useCallback((nodeId: string | null) => {
    send('selection.changed', { nodeId })
  }, [send])

  const sendNodePosition = useCallback((node: Node) => {
    const patch: GraphPatch = { operation: 'node.position', nodeId: node.id, position: node.position }
    send('graph.patch', { patch }, crypto.randomUUID())
  }, [send])

  const sendGraphSaved = useCallback((version: number) => {
    send('graph.saved', { version })
  }, [send])

  return useMemo(
    () => ({ sendCursor, sendSelection, sendNodePosition, sendGraphSaved }),
    [sendCursor, sendSelection, sendNodePosition, sendGraphSaved],
  )
}

function toPresence(session: CollaborationSession) {
  return { ...session }
}

function isCursor(value: unknown): value is { x: number; y: number; viewport: { x: number; y: number; zoom: number } } {
  if (!value || typeof value !== 'object') return false
  const cursor = value as { x?: unknown; y?: unknown; viewport?: unknown }
  return typeof cursor.x === 'number' && typeof cursor.y === 'number'
}

function isGraphPatch(value: unknown): value is GraphPatch {
  if (!value || typeof value !== 'object') return false
  const patch = value as { operation?: unknown }
  return patch.operation === 'node.position' || patch.operation === 'graph.replace'
}
