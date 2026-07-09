import { useMemo, useState } from 'react'
import { Copy, Check } from 'lucide-react'
import type { RendererProps } from './types'

export function JsonRenderer({ artifact }: RendererProps) {
  const payload = artifact.data?.data ?? artifact.data
  const [copied, setCopied] = useState(false)
  const text = useMemo(() => JSON.stringify(payload, null, 2), [payload])
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1200)
    } catch {
      /* noop */
    }
  }
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-white/5 px-4 py-2 text-[11px] uppercase tracking-wider text-white/50">
        <span>JSON</span>
        <button
          onClick={copy}
          className="flex items-center gap-1 rounded-[6px] px-2 py-1 text-[11px] hover:bg-white/[0.06] hover:text-white"
        >
          {copied ? <Check size={11} /> : <Copy size={11} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="flex-1 overflow-auto bg-black/40 px-4 py-3 font-mono text-[12.5px] leading-[1.6] text-white/85">
        {text}
      </pre>
    </div>
  )
}
