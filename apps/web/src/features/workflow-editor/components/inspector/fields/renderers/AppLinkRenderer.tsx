import { useState } from 'react'
import { Check, Copy, ExternalLink } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { slugifyAppUrl } from '@/features/public-app/utils/slug'
import { useWorkflowEditorStore } from '../../../../stores/workflowEditorStore'
import type { RendererProps } from '../types'

/**
 * Read-only "public link" field for the Chat App trigger. The slug is
 * auto-derived (app_slug override → title), mirroring the backend's
 * resolution, so the user never types a slug — they copy or open the
 * link. Shows live/offline state from the workflow's active flag.
 */
export function AppLinkRenderer({ properties }: RendererProps) {
  const wsSlug = useWorkspaceStore(s => s.currentWorkspace?.slug ?? '')
  const isActive = useWorkflowEditorStore(s => Boolean(s.workflow?.is_active))
  const workflowName = useWorkflowEditorStore(s => s.workflow?.name ?? '')
  const [copied, setCopied] = useState(false)

  const raw =
    (properties.app_slug as string) ||
    (properties.title as string) ||
    workflowName ||
    'app'
  const href = `/apps/${wsSlug}/${slugifyAppUrl(raw)}`
  const absolute = typeof window !== 'undefined'
    ? new URL(href, window.location.origin).toString()
    : href

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(absolute)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5 rounded-[8px] border border-[var(--border-faint)] bg-[var(--bg)] px-2.5 py-1.5">
        <span
          className={cn(
            'h-1.5 w-1.5 shrink-0 rounded-full',
            isActive ? 'bg-[var(--ok)]' : 'bg-[var(--text-faint)]',
          )}
          title={isActive ? 'Live' : 'Offline — activate to publish'}
        />
        <span className="min-w-0 flex-1 truncate font-mono text-[11.5px] text-[var(--text)]" title={absolute}>
          {href}
        </span>
        <button
          type="button"
          onClick={copy}
          className="shrink-0 rounded-[5px] p-1 text-[var(--text-faint)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
          title="Copy link"
          aria-label="Copy link"
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
        </button>
        <a
          href={href}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 rounded-[5px] p-1 text-[var(--text-faint)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
          title="Open"
          aria-label="Open link"
        >
          <ExternalLink size={12} />
        </a>
      </div>
      <p className="text-[10.5px] leading-relaxed text-[var(--text-faint)]">
        {isActive
          ? 'Live — anyone with the link can chat. The slug follows the app title.'
          : 'Activate to publish this page. The slug follows the app title.'}
      </p>
    </div>
  )
}
