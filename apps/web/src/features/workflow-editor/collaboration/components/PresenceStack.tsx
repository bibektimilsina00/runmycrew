import { useShallow } from 'zustand/react/shallow'
import { useCollaborationStore } from '../collaborationStore'

/**
 * Floating "who's here" pill — a thin glass bar containing an avatar
 * pile and a live connection dot. Sits on the canvas's top-left corner.
 *
 * Stack rules:
 *   - up to 4 visible avatars, overflow rendered as a "+N" chip
 *   - each avatar wears a 2px ring in the peer's broadcast color so
 *     the same color used by their cursor + selection ring shows up
 *     here too (helps users connect the dots between the three UIs)
 *
 * Renders nothing when there are no peers — solo editing should feel
 * solo, not "you and zero collaborators".
 */
const MAX_VISIBLE = 4

export function PresenceStack() {
  // useShallow keeps Zustand from re-rendering us every commit just
  // because Object.values returned a freshly-allocated array — without
  // it the selector tripped React #185 (max update depth) the moment
  // a peer joined.
  const peers = useCollaborationStore(
    useShallow((s) => Object.values(s.peers).map((p) => p.session)),
  )
  const connected = useCollaborationStore((s) => s.connected)
  if (peers.length === 0) return null

  const visible = peers.slice(0, MAX_VISIBLE)
  const overflow = peers.length - visible.length

  return (
    <div
      className="flex items-center gap-2.5 rounded-full border border-[var(--border-soft)] bg-[var(--bg-2)]/85 px-2.5 py-1.5 backdrop-blur-md shadow-[var(--shadow-float)]"
      role="group"
      aria-label="Collaborators on this workflow"
    >
      {/* Live status dot — soft pulse while connected so the bar reads
          as "active" without the user thinking about WebSockets. */}
      <span className="relative inline-flex h-[8px] w-[8px]" aria-hidden>
        <span
          className={
            connected
              ? 'absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--ok)] opacity-60'
              : 'hidden'
          }
        />
        <span
          className={
            'relative inline-flex h-[8px] w-[8px] rounded-full ' +
            (connected ? 'bg-[var(--ok)]' : 'bg-[var(--text-dim)]')
          }
        />
      </span>

      <div className="flex items-center -space-x-2">
        {visible.map((p) => (
          <Avatar key={p.session_id} name={p.user_name} color={p.color} url={p.avatar_url ?? null} />
        ))}
        {overflow > 0 && (
          <span
            className="inline-flex h-7 w-7 items-center justify-center rounded-full border-2 border-[var(--bg-2)] bg-[var(--surface-2)] text-[10.5px] font-semibold text-[var(--text-mute)]"
            title={`${overflow} more ${overflow === 1 ? 'collaborator' : 'collaborators'}`}
          >
            +{overflow}
          </span>
        )}
      </div>

      <span className="pr-1 text-[11.5px] font-medium text-[var(--text-mute)]">
        {peers.length} {peers.length === 1 ? 'collaborator' : 'collaborators'}
      </span>
    </div>
  )
}

function Avatar({
  name,
  color,
  url,
}: {
  name: string
  color: string
  url: string | null
}) {
  const initial = name.charAt(0).toUpperCase()
  return (
    <span
      title={name}
      className="group relative inline-flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-semibold text-white"
      style={{
        backgroundColor: color,
        // 2px ring in the peer's accent color + a tight bg-2 spacer so
        // overlapping avatars don't smear into each other.
        boxShadow: `0 0 0 2px var(--bg-2), 0 0 0 3.5px ${color}aa`,
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
      {/* Hover label — opt-in tooltip that's nicer than the native
          one, but only on a deliberate hover so it doesn't show for
          every pointer-passing event. */}
      <span
        className="pointer-events-none absolute -bottom-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-[var(--bg)] px-2 py-[3px] text-[10.5px] font-medium text-[var(--text)] opacity-0 shadow-[var(--shadow-float)] transition-opacity duration-150 group-hover:opacity-100"
      >
        {name}
      </span>
    </span>
  )
}
