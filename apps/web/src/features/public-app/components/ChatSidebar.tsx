import { MessageSquare, PanelLeftClose, PanelLeftOpen, SquarePen } from 'lucide-react'
import { cn } from '@/lib/cn'
import { AppLogo } from './AppLogo'
import type { SessionSummary } from '../types/publicAppTypes'

interface ChatSidebarProps {
  title: string
  logoUrl?: string
  sessions: SessionSummary[]
  activeId: string | null
  collapsed: boolean
  onToggleCollapsed: () => void
  onNewChat: () => void
  onSelect: (id: string) => void
}

function relTime(iso: string): string {
  const then = new Date(iso).getTime()
  if (!then) return ''
  const diff = Date.now() - then
  const min = 60_000
  if (diff < min) return 'now'
  if (diff < 60 * min) return `${Math.floor(diff / min)}m`
  if (diff < 24 * 60 * min) return `${Math.floor(diff / (60 * min))}h`
  return `${Math.floor(diff / (24 * 60 * min))}d`
}

/**
 * ChatGPT-style conversation rail. New chat on top, recents below,
 * active row highlighted. Collapses to a slim strip. Empty drafts
 * (0 messages) are hidden unless they're the active conversation, so
 * mashing "New chat" doesn't litter the list.
 */
export function ChatSidebar({
  title,
  logoUrl,
  sessions,
  activeId,
  collapsed,
  onToggleCollapsed,
  onNewChat,
  onSelect,
}: ChatSidebarProps) {
  const visible = sessions.filter(s => s.message_count > 0 || s.id === activeId)

  if (collapsed) {
    return (
      <aside className="flex h-full w-[52px] shrink-0 flex-col items-center gap-2 border-r border-white/5 bg-black/20 py-3">
        <AppLogo src={logoUrl} size={30} />
        <button
          onClick={onToggleCollapsed}
          className="mt-1 flex h-8 w-8 items-center justify-center rounded-[8px] text-white/50 transition hover:bg-white/[0.06] hover:text-white"
          title="Open sidebar"
        >
          <PanelLeftOpen size={15} />
        </button>
        <button
          onClick={onNewChat}
          className="flex h-8 w-8 items-center justify-center rounded-[8px] text-white/50 transition hover:bg-white/[0.06] hover:text-white"
          title="New chat"
        >
          <SquarePen size={15} />
        </button>
      </aside>
    )
  }

  return (
    <aside className="flex h-full w-[260px] shrink-0 flex-col border-r border-white/5 bg-black/20">
      <div className="flex items-center gap-2.5 px-3 pb-2 pt-3">
        <AppLogo src={logoUrl} size={28} />
        <span className="min-w-0 flex-1 truncate text-[13.5px] font-semibold text-white/90">
          {title}
        </span>
        <button
          onClick={onToggleCollapsed}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[7px] text-white/40 transition hover:bg-white/[0.06] hover:text-white"
          title="Collapse sidebar"
        >
          <PanelLeftClose size={14} />
        </button>
      </div>

      <div className="px-2 pb-1">
        <button
          onClick={onNewChat}
          className="flex w-full items-center gap-2 rounded-[9px] border border-white/8 bg-white/[0.03] px-2.5 py-2 text-[12.5px] font-medium text-white/85 transition hover:bg-white/[0.07]"
        >
          <SquarePen size={13} />
          New chat
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-3 pt-2">
        {visible.length > 0 && (
          <div className="px-1.5 pb-1 text-[10.5px] font-semibold uppercase tracking-wider text-white/30">
            Recents
          </div>
        )}
        <div className="flex flex-col gap-0.5">
          {visible.map(s => (
            <button
              key={s.id}
              onClick={() => onSelect(s.id)}
              className={cn(
                'group flex w-full items-center gap-2 rounded-[8px] px-2 py-1.5 text-left transition-colors',
                s.id === activeId
                  ? 'bg-white/[0.08] text-white'
                  : 'text-white/60 hover:bg-white/[0.05] hover:text-white/85',
              )}
            >
              <MessageSquare size={12} className="shrink-0 opacity-50" />
              <span className="min-w-0 flex-1 truncate text-[12.5px] leading-snug">
                {s.title}
              </span>
              <span className="shrink-0 text-[10px] text-white/25">
                {relTime(s.last_seen_at)}
              </span>
            </button>
          ))}
          {visible.length === 0 && (
            <p className="px-1.5 py-3 text-[11.5px] text-white/30">
              No conversations yet.
            </p>
          )}
        </div>
      </div>
    </aside>
  )
}
