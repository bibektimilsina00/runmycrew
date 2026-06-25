import { useEffect, useCallback } from 'react'
import { useAuthStore } from '@/features/auth/store/authStore'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import type { Edge, Node } from 'reactflow'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import { CollaborationClient } from './collaborationClient'
import { useCollaborationStore } from './collaborationStore'
import type { ClientEvent, ServerEvent } from './types'

/** Window in ms after applying a remote patch during which we treat
 *  any local graph change as the echo of that patch and skip
 *  re-broadcasting. 250ms is enough to ride out React's batched render
 *  + the `applyNodeChanges` settle. */
const REMOTE_ECHO_WINDOW_MS = 250

/**
 * Owns the per-workflow collaboration WebSocket lifecycle.
 *
 * Must be mounted exactly once per editor (in `CollaborationLayer`);
 * other components read the resulting senders via
 * `useCollaborationSenders` so we never open a second socket.
 */
export function useCollaborationLifecycle(workflowId: string | undefined) {
  const token = useAuthStore((s) => s.token)
  const workspaceId = useWorkspaceStore((s) => s.currentWorkspaceId)

  const setClient = useCollaborationStore((s) => s.setClient)
  const setOwn = useCollaborationStore((s) => s.setOwn)
  const setConnected = useCollaborationStore((s) => s.setConnected)
  const setSnapshot = useCollaborationStore((s) => s.setSnapshot)
  const upsertPeer = useCollaborationStore((s) => s.upsertPeer)
  const removePeer = useCollaborationStore((s) => s.removePeer)
  const setCursor = useCollaborationStore((s) => s.setCursor)
  const setSelection = useCollaborationStore((s) => s.setSelection)
  const setTyping = useCollaborationStore((s) => s.setTyping)
  const reset = useCollaborationStore((s) => s.reset)

  useEffect(() => {
    if (!workflowId || !token || !workspaceId) return
    reset()

    const handleEvent = (event: ServerEvent) => {
      switch (event.type) {
        case 'session.ready':
          if (event.session) setOwn(event.session)
          break
        case 'presence.snapshot':
          setSnapshot(event.sessions ?? [])
          break
        case 'presence.joined':
          if (event.session) upsertPeer(event.session)
          break
        case 'presence.left':
          if (event.session) removePeer(event.session.session_id)
          break
        case 'cursor.moved': {
          const id = event.session?.session_id
          const payload = event.payload as { x?: number; y?: number } | undefined
          if (id && payload && typeof payload.x === 'number' && typeof payload.y === 'number') {
            if (event.session) upsertPeer(event.session)
            setCursor(id, { x: payload.x, y: payload.y })
          }
          break
        }
        case 'selection.changed': {
          const id = event.session?.session_id
          const payload = event.payload as { nodeIds?: string[] } | undefined
          if (id) {
            if (event.session) upsertPeer(event.session)
            setSelection(id, payload?.nodeIds ?? [])
          }
          break
        }
        case 'typing.changed': {
          const id = event.session?.session_id
          const payload = event.payload as { nodeId?: string | null } | undefined
          if (id) {
            if (event.session) upsertPeer(event.session)
            setTyping(id, payload?.nodeId ?? null)
          }
          break
        }
        case 'graph.patch': {
          // Last-write-wins: peer broadcasts a full graph snapshot, we
          // replace ours. `markApplyingRemote` opens a short window
          // during which the local change watcher in CollaborationLayer
          // suppresses its re-broadcast, breaking the feedback loop.
          const payload = event.payload as
            | { nodes?: Node[]; edges?: Edge[] }
            | undefined
          if (!payload) break
          useCollaborationStore.getState().markApplyingRemote(REMOTE_ECHO_WINDOW_MS)
          const editor = useWorkflowEditorStore.getState()
          if (payload.nodes) editor.setNodes(payload.nodes)
          if (payload.edges) editor.setEdges(payload.edges)
          break
        }
        case 'graph.saved':
          // Notification only — DB save is the source of truth on this
          // side. Nothing to do beyond surfacing it later in the UI.
          break
        case 'error':
          console.warn('[collab] server error', event.payload)
          break
      }
    }

    const client = new CollaborationClient({
      workflowId,
      workspaceId,
      token,
      onEvent: handleEvent,
      onOpen: () => setConnected(true),
      onClose: () => setConnected(false),
    })
    setClient(client)
    client.connect()

    return () => {
      client.disconnect()
      setClient(null)
      reset()
    }
  }, [
    workflowId,
    token,
    workspaceId,
    reset,
    setClient,
    setOwn,
    setConnected,
    setSnapshot,
    upsertPeer,
    removePeer,
    setCursor,
    setSelection,
    setTyping,
  ])
}

/**
 * Sender API for components that want to broadcast their own activity
 * (cursor moves, selection changes, typing). Reads the singleton
 * client from the store, so it's safe to call from anywhere in the
 * editor regardless of mount order.
 */
export function useCollaborationSenders() {
  const send = useCallback((event: ClientEvent) => {
    useCollaborationStore.getState().client?.send(event)
  }, [])

  const sendCursor = useCallback(
    (pos: { x: number; y: number }) => send({ type: 'cursor.moved', payload: pos }),
    [send],
  )
  const sendSelection = useCallback(
    (nodeIds: string[]) => send({ type: 'selection.changed', payload: { nodeIds } }),
    [send],
  )
  const sendTyping = useCallback(
    (nodeId: string | null) => send({ type: 'typing.changed', payload: { nodeId } }),
    [send],
  )
  const sendGraphPatch = useCallback(
    (graph: { nodes: Node[]; edges: Edge[] }) =>
      send({ type: 'graph.patch', payload: graph }),
    [send],
  )

  return { sendCursor, sendSelection, sendTyping, sendGraphPatch }
}
