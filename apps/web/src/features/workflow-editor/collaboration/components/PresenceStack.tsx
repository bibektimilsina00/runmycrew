import { useShallow } from 'zustand/react/shallow'
import { useCollaborationStore } from '../collaborationStore'
import type { PeerSession } from '../types'

/**
 * Compact presence pill — live dot + avatar pile, nothing else.
 *
 * Includes the local user's own session first, then peers, so users
 * see their own avatar / color in the same row as everyone else's.
 * That mirrors how Figma / Linear / Notion render presence and gives
 * the user a stable visual anchor to the color their cursor is being
 * drawn in on every peer's screen.
 *
 * Renders nothing when nobody is here (no own session yet, no peers).
 */
const MAX_AVATARS = 5

export function PresenceStack() {
  // Same useShallow dance as the other selectors — without it, the
  // freshly-allocated array trips a re-render storm under Zustand v5.
  const peers = useCollaborationStore(
    useShallow((s) => Object.values(s.peers).map((p) => p.session)),
  )
  const own = useCollaborationStore((s) => s.own)
  const connected = useCollaborationStore((s) => s.connected)
  // Render nothing when the room is just you — the pill is a
  // collaboration indicator, not a permanent toolbar element. It
  // reappears the moment a peer joins.
  if (!own || peers.length === 0) return null

  const sessions: PeerSession[] = [own, ...peers]
  const visible = sessions.slice(0, MAX_AVATARS)
  const overflow = sessions.length - visible.length

  return (
    <div
      className="flex items-center gap-1.5 rounded-full border border-[var(--border-faint)] bg-[var(--bg-2)]/85 px-1.5 py-1 backdrop-blur-md shadow-[var(--shadow-float)]"
      role="group"
      aria-label="Collaborators on this workflow"
    >
      <span className="relative inline-flex h-[6px] w-[6px] ml-1" aria-hidden>
        <span
          className={
            connected
              ? 'absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--ok)] opacity-60'
              : 'hidden'
          }
        />
        <span
          className={
            'relative inline-flex h-[6px] w-[6px] rounded-full ' +
            (connected ? 'bg-[var(--ok)]' : 'bg-[var(--text-dim)]')
          }
        />
      </span>

      <div className="flex items-center -space-x-1.5">
        {visible.map((s, i) => (
          <Avatar
            key={s.session_id}
            name={s.user_name}
            color={s.color}
            url={s.avatar_url ?? null}
            isSelf={i === 0}
          />
        ))}
        {overflow > 0 && (
          <span
            className="inline-flex h-[22px] min-w-[22px] items-center justify-center rounded-full border-2 border-[var(--bg-2)] bg-[var(--surface-2)] px-1 text-[9.5px] font-semibold text-[var(--text-mute)]"
            title={`${overflow} more`}
          >
            +{overflow}
          </span>
        )}
      </div>
    </div>
  )
}

function Avatar({
  name,
  color,
  url,
  isSelf,
}: {
  name: string
  color: string
  url: string | null
  isSelf: boolean
}) {
  const initial = name.charAt(0).toUpperCase()
  return (
    <span
      title={isSelf ? `${name} (you)` : name}
      className="group relative inline-flex h-[22px] w-[22px] items-center justify-center rounded-full text-[10px] font-semibold text-white"
      style={{
        backgroundColor: color,
        boxShadow: `0 0 0 2px var(--bg-2), 0 0 0 3px ${color}aa`,
      }}
    >
      {url ? (
        <img
          src={url}
          alt={name}
          className="h-full w-full rounded-full object-cover"
          referrerPolicy="no-referrer"
        />
      ) : (
        initial
      )}
      <span
        className="pointer-events-none absolute -bottom-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-[var(--bg)] px-2 py-[3px] text-[10.5px] font-medium text-[var(--text)] opacity-0 shadow-[var(--shadow-float)] transition-opacity duration-150 group-hover:opacity-100"
      >
        {isSelf ? `${name} (you)` : name}
      </span>
    </span>
  )
}
