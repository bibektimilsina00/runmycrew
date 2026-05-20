import { create } from 'zustand'

export interface PresenceEntry {
  session_id: string
  user_id: string
  user_name: string
  avatar_url: string | null
  color: string
  connected_at: string
}

export interface CursorPosition {
  x: number
  y: number
  viewport: { x: number; y: number; zoom: number }
}

export type WsStatus = 'disconnected' | 'connecting' | 'connected'

interface CollaborationState {
  // Connected users keyed by session_id
  presence: Record<string, PresenceEntry>
  // Cursor positions keyed by session_id
  cursors: Record<string, CursorPosition>
  // Which node each session has selected: session_id → node_id
  nodeSelections: Record<string, string>
  // Which field each session is typing in: session_id → node_id:field_name
  typingIndicators: Record<string, string>

  wsStatus: WsStatus
  mySessionId: string | null
  myUserId: string | null   // tracks current user's id to filter ALL their own sessions

  // Actions
  setPresence: (entry: PresenceEntry) => void
  removePresence: (sessionId: string) => void
  updateCursor: (sessionId: string, pos: CursorPosition) => void
  setNodeSelection: (sessionId: string, nodeId: string | null) => void
  setTypingIndicator: (sessionId: string, indicator: string | null) => void
  setWsStatus: (status: WsStatus) => void
  setMySessionId: (id: string | null) => void
  setMyUserId: (id: string | null) => void
  reset: () => void

  // Derived helpers
  getNodeSelectionColor: (nodeId: string) => string | null
  /** Unique OTHER users — deduped by user_id, self excluded, latest session wins */
  getOtherUsers: () => PresenceEntry[]
}

const INITIAL_STATE = {
  presence: {},
  cursors: {},
  nodeSelections: {},
  typingIndicators: {},
  wsStatus: 'disconnected' as WsStatus,
  mySessionId: null,
  myUserId: null,
}

export const useCollaborationStore = create<CollaborationState>((set, get) => ({
  ...INITIAL_STATE,

  setPresence: (entry) =>
    set(s => ({ presence: { ...s.presence, [entry.session_id]: entry } })),

  removePresence: (sessionId) =>
    set(s => {
      const { [sessionId]: _, ...rest } = s.presence
      const { [sessionId]: _c, ...cursors } = s.cursors
      const { [sessionId]: _n, ...nodeSelections } = s.nodeSelections
      const { [sessionId]: _t, ...typingIndicators } = s.typingIndicators
      return { presence: rest, cursors, nodeSelections, typingIndicators }
    }),

  updateCursor: (sessionId, pos) =>
    set(s => ({ cursors: { ...s.cursors, [sessionId]: pos } })),

  setNodeSelection: (sessionId, nodeId) =>
    set(s => {
      if (nodeId === null) {
        const { [sessionId]: _, ...rest } = s.nodeSelections
        return { nodeSelections: rest }
      }
      return { nodeSelections: { ...s.nodeSelections, [sessionId]: nodeId } }
    }),

  setTypingIndicator: (sessionId, indicator) =>
    set(s => {
      if (indicator === null) {
        const { [sessionId]: _, ...rest } = s.typingIndicators
        return { typingIndicators: rest }
      }
      return { typingIndicators: { ...s.typingIndicators, [sessionId]: indicator } }
    }),

  setWsStatus: (wsStatus) => set({ wsStatus }),
  setMySessionId: (mySessionId) => set({ mySessionId }),
  setMyUserId: (myUserId) => set({ myUserId }),
  reset: () => set(INITIAL_STATE),

  getNodeSelectionColor: (nodeId) => {
    const { nodeSelections, presence, mySessionId } = get()
    for (const [sessionId, selectedNodeId] of Object.entries(nodeSelections)) {
      if (selectedNodeId === nodeId && sessionId !== mySessionId) {
        return presence[sessionId]?.color ?? null
      }
    }
    return null
  },

  getOtherUsers: () => {
    const { presence, myUserId } = get()
    // Exclude all sessions belonging to the current user
    const others = Object.values(presence).filter(e => e.user_id !== myUserId)
    // Dedupe by user_id — keep the session with the latest connected_at
    const byUserId = new Map<string, PresenceEntry>()
    for (const entry of others) {
      const existing = byUserId.get(entry.user_id)
      if (!existing || entry.connected_at > existing.connected_at) {
        byUserId.set(entry.user_id, entry)
      }
    }
    return Array.from(byUserId.values())
  },
}))
