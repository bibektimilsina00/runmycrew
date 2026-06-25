import { useCollaborationStore } from '../collaborationStore'

/**
 * Avatar pile shown floating near the editor toolbar. Up to 4 peer
 * avatars are stacked; anything beyond gets a "+N" overflow chip so
 * the stack never grows past a fixed width.
 */
const MAX_VISIBLE = 4

export function PresenceStack() {
  const peers = useCollaborationStore((s) =>
    Object.values(s.peers).map((p) => p.session),
  )
  if (peers.length === 0) return null

  const visible = peers.slice(0, MAX_VISIBLE)
  const overflow = peers.length - visible.length

  return (
    <div className="flex items-center -space-x-2">
      {visible.map((p) => (
        <Avatar key={p.session_id} name={p.user_name} color={p.color} url={p.avatar_url ?? null} />
      ))}
      {overflow > 0 && (
        <span
          className="inline-flex h-7 w-7 items-center justify-center rounded-full border-2 border-[var(--bg)] bg-[var(--surface-2)] text-[10px] font-semibold text-[var(--text-mute)]"
          title={`${overflow} more ${overflow === 1 ? 'collaborator' : 'collaborators'}`}
        >
          +{overflow}
        </span>
      )}
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
      className="relative inline-flex h-7 w-7 items-center justify-center rounded-full border-2 text-[11px] font-semibold text-white"
      style={{ backgroundColor: color, borderColor: 'var(--bg)' }}
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
    </span>
  )
}
