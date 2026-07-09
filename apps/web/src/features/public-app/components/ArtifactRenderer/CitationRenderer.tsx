import { ExternalLink, Quote } from 'lucide-react'
import type { RendererProps } from './types'

export function CitationRenderer({ artifact }: RendererProps) {
  const url = String(artifact.data?.url ?? '')
  const title = String(artifact.data?.title ?? artifact.title ?? '')
  const snippet = String(artifact.data?.snippet ?? '')
  return (
    <div className="p-6">
      <a
        href={url}
        target="_blank"
        rel="noreferrer"
        className="group flex flex-col gap-2 rounded-[12px] border border-white/10 bg-white/[0.03] p-4 transition hover:border-white/20 hover:bg-white/[0.05]"
      >
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-white/50">
          <Quote size={12} />
          Citation
          <ExternalLink size={11} className="ml-auto opacity-0 transition group-hover:opacity-70" />
        </div>
        <div className="text-[14px] font-semibold text-white">{title || url}</div>
        {snippet && <p className="text-[12.5px] leading-relaxed text-white/60">{snippet}</p>}
        <div className="truncate text-[11px] text-white/40">{url}</div>
      </a>
    </div>
  )
}
