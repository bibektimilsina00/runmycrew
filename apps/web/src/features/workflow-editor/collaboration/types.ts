/**
 * Wire-level event types mirroring the backend collaboration schema
 * (apps/api/app/features/collaboration/schemas.py). Keep these in
 * lockstep — adding a new event type requires both sides.
 */

export type ClientEventType =
  | 'cursor.moved'
  | 'selection.changed'
  | 'typing.changed'
  | 'graph.patch'
  | 'graph.saved'
  | 'heartbeat'

export type ServerEventType =
  | 'session.ready'
  | 'presence.snapshot'
  | 'presence.joined'
  | 'presence.left'
  | 'cursor.moved'
  | 'selection.changed'
  | 'typing.changed'
  | 'graph.patch'
  | 'graph.saved'
  | 'error'

export interface PeerSession {
  session_id: string
  user_id: string
  user_name: string
  avatar_url?: string | null
  color: string
  connected_at: string
}

export interface ClientEvent {
  type: ClientEventType
  payload?: Record<string, unknown>
  patch_id?: string
}

export interface ServerEvent {
  type: ServerEventType
  session?: PeerSession
  sessions?: PeerSession[]
  payload?: Record<string, unknown>
  patch_id?: string
}

/** Per-peer ephemeral state we track locally for rendering. */
export interface PeerState {
  session: PeerSession
  cursor: { x: number; y: number } | null
  selectedNodeIds: string[]
  typingNodeId: string | null
}
