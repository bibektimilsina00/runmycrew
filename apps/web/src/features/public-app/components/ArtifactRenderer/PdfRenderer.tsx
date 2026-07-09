import { Download, FileText } from 'lucide-react'
import type { RendererProps } from './types'

/**
 * Browsers can render PDFs in an iframe when the URL points at one.
 * We give a header row + iframe body so the canvas doesn't lose chrome.
 */
export function PdfRenderer({ artifact }: RendererProps) {
  const url = String(artifact.data?.url ?? '')
  const filename = String(artifact.data?.filename ?? artifact.title ?? 'document.pdf')
  if (!url) return <div className="p-6 text-[13px] text-white/50">No PDF URL</div>
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-white/5 bg-black/30 px-4 py-2">
        <FileText size={14} className="text-white/60" />
        <div className="min-w-0 flex-1 truncate text-[12.5px] text-white/80">{filename}</div>
        <a
          href={url}
          download={filename}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 rounded-[6px] border border-white/10 bg-white/[0.03] px-2 py-1 text-[11px] text-white/70 hover:text-white"
        >
          <Download size={11} />
          Save
        </a>
      </div>
      <iframe title={filename} src={url} className="flex-1 border-0 bg-white" />
    </div>
  )
}
