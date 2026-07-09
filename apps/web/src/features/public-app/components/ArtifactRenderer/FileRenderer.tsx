import { Download, File as FileIcon } from 'lucide-react'
import type { RendererProps } from './types'

function bytes(n: number): string {
  if (!n) return '—'
  const k = 1024
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(n) / Math.log(k))
  return `${(n / Math.pow(k, i)).toFixed(1)} ${units[i]}`
}

export function FileRenderer({ artifact }: RendererProps) {
  const url = String(artifact.data?.url ?? '')
  const filename = String(artifact.data?.filename ?? artifact.title ?? 'file')
  const mime = String(artifact.data?.mime ?? '')
  const size = Number(artifact.data?.size_bytes ?? 0)
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="flex w-full max-w-[420px] flex-col items-start gap-3 rounded-[14px] border border-white/10 bg-white/[0.03] p-5">
        <span className="flex h-11 w-11 items-center justify-center rounded-[10px] bg-white/[0.06] text-white/70">
          <FileIcon size={20} />
        </span>
        <div className="w-full">
          <div className="truncate text-[15px] font-medium text-white">{filename}</div>
          <div className="mt-0.5 text-[11.5px] text-white/50">
            {mime || 'file'} · {bytes(size)}
          </div>
        </div>
        {url && (
          <a
            href={url}
            download={filename}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-flex items-center gap-1.5 rounded-[8px] px-3 py-1.5 text-[12.5px] font-medium text-white transition hover:brightness-110"
            style={{ background: 'var(--app-accent, #8b5cf6)' }}
          >
            <Download size={12} />
            Download
          </a>
        )}
      </div>
    </div>
  )
}
