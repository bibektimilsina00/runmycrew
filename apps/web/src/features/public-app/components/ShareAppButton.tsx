import { useEffect, useRef, useState } from 'react'
import { Check, Copy, ExternalLink, Globe } from 'lucide-react'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { slugifyAppUrl } from '../utils/slug'

interface ShareAppButtonProps {
  workflowId: string
  appSlug: string
}

/**
 * Compact "Live" chip for the editor action bar. The full URL lives in
 * a click-popover (copy + open) instead of inline — the raw path was
 * wrapping to two lines and crowding the Activate/Run buttons.
 */
export function ShareAppButton({ appSlug }: ShareAppButtonProps) {
  const workspace = useWorkspaceStore(s => s.currentWorkspace)
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const wsSlug = workspace?.slug || ''
  const slug = slugifyAppUrl(appSlug)
  const href = `/apps/${wsSlug}/${slug}`
  const absolute = typeof window !== 'undefined'
    ? new URL(href, window.location.origin).toString()
    : href

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(absolute)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* noop */
    }
  }

  if (!wsSlug || !appSlug) return null

  return (
    <div ref={rootRef} className="relative">
      <button
        onClick={() => setOpen(v => !v)}
        className="flex h-7 items-center gap-1.5 rounded-[7px] border border-[var(--border-faint)] bg-[var(--surface)] px-2 text-[11.5px] font-medium text-[var(--text-mute)] transition-colors hover:border-[var(--border)] hover:text-[var(--text)]"
        title="Live app URL"
        aria-expanded={open}
      >
        <span className="relative flex h-1.5 w-1.5">
          <span className="absolute inset-0 rounded-full bg-[var(--ok)]" />
          <span className="absolute inset-0 animate-ping rounded-full bg-[var(--ok)] opacity-60" />
        </span>
        Live
      </button>

      {open && (
        <div className="absolute right-0 top-9 z-40 flex w-[300px] flex-col gap-2 rounded-[10px] border border-[var(--border-faint)] bg-[var(--bg-2)] p-3 shadow-[0_12px_32px_-8px_rgba(0,0,0,0.6)]">
          <div className="flex items-center gap-1.5 text-[10.5px] font-semibold uppercase tracking-wider text-[var(--text-faint)]">
            <Globe size={11} />
            Hosted app URL
          </div>
          <div className="truncate rounded-[7px] border border-[var(--border-faint)] bg-[var(--bg)] px-2.5 py-1.5 font-mono text-[11px] text-[var(--text)]" title={absolute}>
            {href}
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={copy}
              className="flex h-7 flex-1 items-center justify-center gap-1.5 rounded-[7px] border border-[var(--border-faint)] bg-[var(--surface)] text-[11.5px] text-[var(--text-mute)] transition-colors hover:text-[var(--text)]"
            >
              {copied ? <Check size={11} /> : <Copy size={11} />}
              {copied ? 'Copied' : 'Copy link'}
            </button>
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="flex h-7 flex-1 items-center justify-center gap-1.5 rounded-[7px] border border-[var(--border-faint)] bg-[var(--surface)] text-[11.5px] text-[var(--text-mute)] transition-colors hover:text-[var(--text)]"
            >
              <ExternalLink size={11} />
              Open
            </a>
          </div>
          <p className="text-[10.5px] leading-relaxed text-[var(--text-faint)]">
            Anyone with the link can chat. Each visitor message runs this graph.
          </p>
        </div>
      )}
    </div>
  )
}
