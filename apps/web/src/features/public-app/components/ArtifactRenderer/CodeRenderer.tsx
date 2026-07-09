import { useState } from 'react'
import { Check, Copy, Download } from 'lucide-react'
import type { RendererProps } from './types'

/**
 * Read-only code block. No highlighter dependency to keep the public
 * bundle lean — monospace + line numbers is enough for the canvas
 * preview. Owner can drop the full file into their own IDE.
 */
export function CodeRenderer({ artifact }: RendererProps) {
  const code = String(artifact.data?.code ?? '')
  const language = String(artifact.data?.language ?? 'text')
  const filename = artifact.data?.filename as string | undefined
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1200)
    } catch {
      /* noop */
    }
  }

  const download = () => {
    const blob = new Blob([code], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename || `snippet.${language === 'text' ? 'txt' : language}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const lines = code.split('\n')

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-white/5 px-4 py-2 text-[11px] uppercase tracking-wider text-white/50">
        <span>{filename ? `${filename} · ${language}` : language}</span>
        <div className="flex items-center gap-1">
          <button
            onClick={copy}
            className="flex items-center gap-1 rounded-[6px] px-2 py-1 text-[11px] hover:bg-white/[0.06] hover:text-white"
            title="Copy"
          >
            {copied ? <Check size={11} /> : <Copy size={11} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button
            onClick={download}
            className="flex items-center gap-1 rounded-[6px] px-2 py-1 text-[11px] hover:bg-white/[0.06] hover:text-white"
            title="Download"
          >
            <Download size={11} />
            Download
          </button>
        </div>
      </div>
      <pre className="flex-1 overflow-auto bg-black/40 px-0 py-3 font-mono text-[12.5px] leading-[1.6] text-white/85">
        {lines.map((line, i) => (
          <div key={i} className="flex px-4">
            <span className="mr-4 min-w-[2.4em] shrink-0 select-none text-right text-white/25">
              {i + 1}
            </span>
            <span className="whitespace-pre">{line || ' '}</span>
          </div>
        ))}
      </pre>
    </div>
  )
}
