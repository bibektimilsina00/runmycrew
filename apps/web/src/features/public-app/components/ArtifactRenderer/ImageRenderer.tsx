import { Download } from 'lucide-react'
import type { RendererProps } from './types'

export function ImageRenderer({ artifact }: RendererProps) {
  const url = String(artifact.data?.url ?? '')
  const alt = String(artifact.data?.alt ?? artifact.title ?? '')
  if (!url) return <div className="p-6 text-[13px] text-white/50">No image URL</div>
  return (
    <div className="relative flex h-full items-center justify-center bg-black/50 p-4">
      <img
        src={url}
        alt={alt}
        className="max-h-full max-w-full rounded-[8px] object-contain shadow-[0_10px_40px_-16px_rgba(0,0,0,0.7)]"
      />
      <a
        href={url}
        download
        target="_blank"
        rel="noreferrer"
        className="absolute right-4 top-4 flex items-center gap-1 rounded-[7px] border border-white/10 bg-black/50 px-2 py-1 text-[11px] text-white/80 backdrop-blur hover:bg-black/70"
      >
        <Download size={11} />
        Save
      </a>
    </div>
  )
}
