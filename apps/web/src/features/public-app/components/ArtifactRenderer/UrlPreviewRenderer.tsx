import { ExternalLink, Globe } from 'lucide-react'
import type { RendererProps } from './types'

/**
 * Sandboxed iframe preview + a summary card at top with URL / title /
 * open-in-new-tab button. Loads external content in an `allow-scripts`
 * sandbox — no `allow-same-origin` so the embedded page can't touch
 * the parent.
 */
export function UrlPreviewRenderer({ artifact }: RendererProps) {
  const url = String(artifact.data?.url ?? '')
  const title = String(artifact.data?.title ?? artifact.title ?? '')
  const description = String(artifact.data?.description ?? '')
  if (!url) return <div className="p-6 text-[13px] text-white/50">No URL</div>

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-white/5 bg-black/30 px-4 py-3">
        <Globe size={14} className="text-white/50" />
        <div className="min-w-0 flex-1">
          <div className="truncate text-[13px] font-medium text-white/90">
            {title || new URL(url).hostname}
          </div>
          <div className="truncate text-[11px] text-white/50">{description || url}</div>
        </div>
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 rounded-[6px] border border-white/10 bg-white/[0.03] px-2 py-1 text-[11px] text-white/70 hover:text-white"
        >
          <ExternalLink size={11} />
          Open
        </a>
      </div>
      <iframe
        title={title || url}
        src={url}
        sandbox="allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
        className="flex-1 border-0 bg-white"
        referrerPolicy="no-referrer"
        loading="lazy"
      />
    </div>
  )
}
