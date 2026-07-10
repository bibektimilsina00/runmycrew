import { useState } from 'react'
import { Check, Copy, ExternalLink } from 'lucide-react'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { slugifyAppUrl } from '../utils/slug'

interface ShareAppButtonProps {
  workflowId: string
  appSlug: string
}

/**
 * Live-URL chip shown next to the Activate/Run buttons whenever the
 * workflow has a ``trigger.chat_app`` node AND is active. No modal —
 * the URL is inferred from the workspace slug + trigger's ``app_slug``.
 */
export function ShareAppButton({ appSlug }: ShareAppButtonProps) {
  const workspace = useWorkspaceStore(s => s.currentWorkspace)
  const [copied, setCopied] = useState(false)

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
    <div className="flex items-center gap-1 rounded-[7px] border border-[var(--border-faint)] bg-[var(--surface)] px-2 py-1 text-[11.5px] text-[var(--text-mute)]">
      <span className="font-mono text-[11px] text-[var(--text)]">
        /apps/{wsSlug}/{slug}
      </span>
      <button
        onClick={copy}
        className="rounded-[5px] p-1 hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
        title="Copy link"
      >
        {copied ? <Check size={11} /> : <Copy size={11} />}
      </button>
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="rounded-[5px] p-1 hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
        title="Open"
      >
        <ExternalLink size={11} />
      </a>
    </div>
  )
}
