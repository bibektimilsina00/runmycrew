import { useCollaborationStore } from '@/stores/collaboration-store'

export function PresenceAvatars() {
  const wsStatus = useCollaborationStore(s => s.wsStatus)
  const getOtherUsers = useCollaborationStore(s => s.getOtherUsers)

  if (wsStatus !== 'connected') return null

  const others = getOtherUsers()
  if (others.length === 0) return null

  const visible = others.slice(0, 5)
  const overflow = others.length - 5

  return (
    <div className="flex items-center gap-1.5" title={`${others.length} other${others.length > 1 ? 's' : ''} viewing`}>
      <div className="flex -space-x-1.5">
        {visible.map(session => (
          <div
            key={session.user_id}
            className="flex size-6 items-center justify-center rounded-full border-2 border-[var(--bg)] text-[10px] font-bold text-white shadow-sm"
            style={{ backgroundColor: session.color }}
            title={session.user_name}
          >
            {session.user_name[0]?.toUpperCase() ?? '?'}
          </div>
        ))}
        {overflow > 0 && (
          <div className="flex size-6 items-center justify-center rounded-full border-2 border-[var(--bg)] bg-[var(--surface-3)] text-[9px] font-bold text-white shadow-sm">
            +{overflow}
          </div>
        )}
      </div>
      <span className="text-[11px] text-[var(--text-muted)]">
        {others.length === 1
          ? `${others[0].user_name.split(' ')[0]} is here`
          : `${others.length} viewing`}
      </span>
    </div>
  )
}
