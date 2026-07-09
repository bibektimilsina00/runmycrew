import { useState } from 'react'
import { Check, Copy, Sparkles } from 'lucide-react'
import type { PublicApp } from '../types/publicAppTypes'

interface AppHeaderProps {
  app: PublicApp
  onNewChat: () => void
}

/**
 * Minimal top strip. Owner logo + title on the left, share + new-chat
 * on the right. Kept intentionally quiet so the workflow's output stays
 * the visual anchor.
 */
export function AppHeader({ app, onNewChat }: AppHeaderProps) {
  const [copied, setCopied] = useState(false)

  const share = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard blocked in some contexts */
    }
  }

  const logo = app.config.logo_url
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b border-white/5 bg-[var(--bg,#0b0b0f)]/85 px-5 py-3 backdrop-blur">
      <div className="flex items-center gap-2.5 min-w-0">
        {logo ? (
          <img src={logo} alt="" className="h-7 w-7 rounded-md object-cover" />
        ) : (
          <span
            className="flex h-7 w-7 items-center justify-center rounded-md text-white/80"
            style={{ background: 'var(--app-accent, #8b5cf6)' }}
          >
            <Sparkles size={14} />
          </span>
        )}
        <div className="min-w-0">
          <div className="truncate text-[14px] font-semibold leading-tight text-white/90">
            {app.title}
          </div>
          {app.description && (
            <div className="truncate text-[11px] text-white/45">{app.description}</div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-1.5">
        <button
          onClick={onNewChat}
          className="rounded-[7px] border border-white/8 bg-white/[0.03] px-2.5 py-1 text-[11.5px] font-medium text-white/70 transition hover:bg-white/[0.06] hover:text-white"
        >
          New chat
        </button>
        <button
          onClick={share}
          className="flex items-center gap-1 rounded-[7px] border border-white/8 bg-white/[0.03] px-2.5 py-1 text-[11.5px] font-medium text-white/70 transition hover:bg-white/[0.06] hover:text-white"
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Share'}
        </button>
      </div>
    </header>
  )
}
