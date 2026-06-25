import { create } from 'zustand'
import type { CollaborationClient } from './collaborationClient'
import type { PeerSession, PeerState } from './types'

/**
 * Ephemeral collaboration state for the currently-open workflow.
 *
 * `peers` is keyed by `session_id` (not `user_id`) so the same user
 * opening the workflow in two tabs shows up as two cursors — that's
 * what they're seeing on their screen, so it matches their mental
 * model. `own` is set once `session.ready` arrives; until then we
 * render nothing peer-related to avoid flashes.
 */
interface CollaborationState {
  own: PeerSession | null
  peers: Record<string, PeerState>
  connected: boolean
  /** Singleton WS client. Owned by the `useCollaboration` lifecycle
   *  hook (mounted once inside `CollaborationLayer`); consumers like
   *  the inspector read it via `useCollaborationSenders` to send their
   *  own events without opening a second socket. */
  client: CollaborationClient | null
  /** Timestamp (perf.now) before which a local graph change is treated
   *  as the echo of a remote patch we just applied — we skip re-broadcast
   *  to break the feedback loop. */
  applyingRemoteUntil: number

  setClient: (client: CollaborationClient | null) => void
  setOwn: (session: PeerSession | null) => void
  setConnected: (connected: boolean) => void
  setSnapshot: (sessions: PeerSession[]) => void
  upsertPeer: (session: PeerSession) => void
  removePeer: (sessionId: string) => void
  setCursor: (sessionId: string, cursor: { x: number; y: number } | null) => void
  setSelection: (sessionId: string, nodeIds: string[]) => void
  setTyping: (sessionId: string, nodeId: string | null) => void
  markApplyingRemote: (windowMs: number) => void
  reset: () => void
}

const EMPTY_PEER = (session: PeerSession): PeerState => ({
  session,
  cursor: null,
  selectedNodeIds: [],
  typingNodeId: null,
})

export const useCollaborationStore = create<CollaborationState>((set) => ({
  own: null,
  peers: {},
  connected: false,
  client: null,
  applyingRemoteUntil: 0,

  setClient: (client) => set({ client }),
  setOwn: (session) => set({ own: session }),
  markApplyingRemote: (windowMs) =>
    set({ applyingRemoteUntil: performance.now() + windowMs }),
  setConnected: (connected) => set({ connected }),

  setSnapshot: (sessions) =>
    set((state) => {
      const next: Record<string, PeerState> = {}
      for (const s of sessions) {
        if (state.own && s.session_id === state.own.session_id) continue
        next[s.session_id] = state.peers[s.session_id] ?? EMPTY_PEER(s)
      }
      return { peers: next }
    }),

  upsertPeer: (session) =>
    set((state) => {
      if (state.own && session.session_id === state.own.session_id) return state
      return {
        peers: {
          ...state.peers,
          [session.session_id]: state.peers[session.session_id] ?? EMPTY_PEER(session),
        },
      }
    }),

  removePeer: (sessionId) =>
    set((state) => {
      if (!(sessionId in state.peers)) return state
      const next = { ...state.peers }
      delete next[sessionId]
      return { peers: next }
    }),

  setCursor: (sessionId, cursor) =>
    set((state) => {
      const peer = state.peers[sessionId]
      if (!peer) return state
      return { peers: { ...state.peers, [sessionId]: { ...peer, cursor } } }
    }),

  setSelection: (sessionId, nodeIds) =>
    set((state) => {
      const peer = state.peers[sessionId]
      if (!peer) return state
      return {
        peers: { ...state.peers, [sessionId]: { ...peer, selectedNodeIds: nodeIds } },
      }
    }),

  setTyping: (sessionId, nodeId) =>
    set((state) => {
      const peer = state.peers[sessionId]
      if (!peer) return state
      return { peers: { ...state.peers, [sessionId]: { ...peer, typingNodeId: nodeId } } }
    }),

  reset: () =>
    set({ own: null, peers: {}, connected: false, client: null, applyingRemoteUntil: 0 }),
}))
