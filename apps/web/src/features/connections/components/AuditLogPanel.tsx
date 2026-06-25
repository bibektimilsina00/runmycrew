import { createPortal } from 'react-dom'
import { Icons } from '@/shared/components/icons'
import { useAuditLog } from '../hooks/useConnections'
import type { Provider } from '../types/connectionsTypes'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'

interface Props {
  providers: Provider[]
  onClose: () => void
}

const ACTION_LABEL: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  'credential.created': {
    label: 'Connected',
    icon: <Icons.Plug style={{ width: 12, height: 12 }} />,
    color: 'text-[var(--ok)]',
  },
  'credential.renamed': {
    label: 'Renamed',
    icon: <Icons.Edit style={{ width: 12, height: 12 }} />,
    color: 'text-[var(--accent)]',
  },
  'credential.deleted': {
    label: 'Disconnected',
    icon: <Icons.Trash style={{ width: 12, height: 12 }} />,
    color: 'text-[var(--err)]',
  },
}

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const mins  = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days  = Math.floor(diff / 86400000)
  if (mins < 1)  return 'just now'
  if (mins < 60) return `${mins}m ago`
  if (hours < 24)return `${hours}h ago`
  if (days < 7)  return `${days}d ago`
  return new Date(isoString).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function AuditLogPanel({ providers, onClose }: Props) {
  const { data: entries = [], isLoading } = useAuditLog(true)
  const providerMap = Object.fromEntries(providers.map(p => [p.id, p]))

  return createPortal(
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[9997] bg-black/30 backdrop-blur-[2px]"
        onClick={onClose}
      />

      {/* Slide-over panel */}
      <div className="fixed top-0 right-0 bottom-0 z-[9998] w-full max-w-[420px] bg-[var(--bg-2)] border-l border-[var(--border-faint)] flex flex-col shadow-[-24px_0_48px_-20px_oklch(0_0_0/0.4)]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-faint)]">
          <div>
            <h3 className="text-[14px] font-semibold text-[var(--text)] tracking-tight">Connection audit log</h3>
            <p className="text-[12px] text-[var(--text-faint)] mt-0.5">All connection changes in this workspace</p>
          </div>
          <button
            onClick={onClose}
            className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[13px]"
          >
            ✕
          </button>
        </div>

        {/* Log list */}
        <div className="flex-1 overflow-y-auto p-5">
          {isLoading ? (
            <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
              <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
              Loading audit log…
            </div>
          ) : entries.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-12 text-center">
              <div className="w-[40px] h-[40px] rounded-full bg-[var(--surface)] flex items-center justify-center">
                <Icons.Activity style={{ width: 18, height: 18, color: 'var(--text-dim)' }} />
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-[13px] font-medium text-[var(--text-mute)]">No activity yet</span>
                <span className="text-[12px] text-[var(--text-faint)]">Actions on connections will appear here.</span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col">
              {entries.map((entry, i) => {
                const meta   = entry.meta as Record<string, string> | null
                const action = ACTION_LABEL[entry.action]
                const provider = providerMap[meta?.type ?? '']
                const userName = entry.user_name || entry.user_email?.split('@')[0] || 'Unknown user'
                const userInitial = userName[0]?.toUpperCase() ?? '?'
                const isLast = i === entries.length - 1

                return (
                  <div key={entry.id} className="flex gap-3 pb-4 relative">
                    {/* Timeline line */}
                    {!isLast && (
                      <div className="absolute left-[14px] top-[28px] bottom-0 w-px bg-[var(--border-faint)]" />
                    )}

                    {/* User avatar */}
                    <div className="w-[28px] h-[28px] rounded-full bg-[var(--surface-3)] border border-[var(--border-soft)] flex items-center justify-center text-[11px] font-semibold text-[var(--text)] shrink-0 z-10">
                      {userInitial}
                    </div>

                    <div className="flex flex-col gap-1 min-w-0 pt-0.5">
                      {/* Action + resource */}
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-[13px] font-medium text-[var(--text)]">{userName}</span>
                        <span className={`inline-flex items-center gap-1 text-[11.5px] font-medium ${action?.color ?? 'text-[var(--text-mute)]'}`}>
                          {action?.icon}
                          {action?.label}
                        </span>
                        <span className="text-[13px] text-[var(--text-mute)] truncate">
                          {entry.resource_name}
                        </span>
                      </div>

                      {/* Extra detail for renames */}
                      {entry.action === 'credential.renamed' && meta && (
                        <div className="flex items-center gap-1.5 text-[11.5px] font-mono text-[var(--text-faint)]">
                          <span className="line-through">{meta.old_name}</span>
                          <span>→</span>
                          <span className="text-[var(--text-mute)]">{meta.new_name}</span>
                        </div>
                      )}

                      {/* Provider tag + timestamp */}
                      <div className="flex items-center gap-2 mt-0.5">
                        {provider && (
                          <span className="inline-flex items-center gap-1 text-[10.5px] font-mono text-[var(--text-dim)] bg-[var(--surface)] border border-[var(--border-faint)] px-2 py-0.5 rounded-[4px] [&_img]:h-[10px] [&_img]:w-[10px] [&_img]:object-contain">
                            {provider.icon_slug && <BrandIcon slug={provider.icon_slug} />}
                            {provider.name}
                          </span>
                        )}
                        <span className="text-[11px] text-[var(--text-dim)] font-mono">
                          {timeAgo(entry.created_at)}
                        </span>
                        {entry.user_email && (
                          <span className="text-[11px] text-[var(--text-dim)] font-mono truncate">
                            · {entry.user_email}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </>,
    document.body
  )
}
