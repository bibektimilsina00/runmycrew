import { useState } from 'react'
import { Check, Copy, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { AppLogo } from './AppLogo'
import type { AppMessage } from '../types/publicAppTypes'

interface MessageBubbleProps {
  message: AppMessage
  streaming?: boolean
  /** App logo for the assistant avatar (config.logo_url). */
  logoUrl?: string
}

/**
 * Borderless assistant messages so the response reads like a document
 * (Claude / ChatGPT style). User messages get a subtle bubble so the
 * turn taking is still legible at a glance. Assistant content renders
 * as GFM markdown — agents speak markdown, plain text read as broken.
 */
export function MessageBubble({ message, streaming, logoUrl }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable */
    }
  }

  if (isUser) {
    return (
      <div className="flex w-full justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-md bg-white/[0.07] px-4 py-2.5 text-[14px] leading-[1.55] text-white/85">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="group flex w-full justify-start gap-3">
      <AppLogo src={logoUrl} size={26} className="mt-0.5 shrink-0" />
      <div className="max-w-[100%] min-w-0 flex-1">
        {message.content ? (
          <div className="prose prose-invert max-w-none text-[15px] leading-[1.65] prose-p:my-2 prose-pre:my-3 prose-pre:rounded-[10px] prose-pre:border prose-pre:border-white/10 prose-pre:bg-black/40 prose-code:text-[13px] prose-headings:mt-4 prose-headings:mb-2 prose-li:my-0.5 prose-table:text-[13.5px]">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        ) : streaming ? (
          <span className="inline-flex items-center gap-2 text-[13px] text-white/40">
            <Loader2 size={12} className="animate-spin" />
            Thinking…
          </span>
        ) : null}

        {streaming && message.content && (
          <span className="mt-1 inline-block h-[13px] w-[7px] animate-pulse bg-[var(--app-accent,#8b5cf6)]" />
        )}

        {message.is_error && (
          <span className="mt-1 block text-[12px] text-red-400/80">Something went wrong.</span>
        )}

        {!streaming && message.content && (
          <button
            onClick={copy}
            className="mt-1.5 flex items-center gap-1 rounded-[6px] px-1.5 py-1 text-[11px] text-white/30 opacity-0 transition-opacity hover:bg-white/[0.06] hover:text-white/60 group-hover:opacity-100"
            title="Copy response"
          >
            {copied ? <Check size={11} /> : <Copy size={11} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        )}
      </div>
    </div>
  )
}
