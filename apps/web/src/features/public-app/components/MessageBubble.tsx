import { Loader2 } from 'lucide-react'
import type { AppMessage } from '../types/publicAppTypes'

interface MessageBubbleProps {
  message: AppMessage
  streaming?: boolean
}

/**
 * Borderless assistant messages so the response reads like a document
 * (Claude / ChatGPT style). User messages get a subtle bubble so the
 * turn taking is still legible at a glance.
 */
export function MessageBubble({ message, streaming }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  return (
    <div
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={
          isUser
            ? 'max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-md bg-white/[0.07] px-4 py-2.5 text-[14px] leading-[1.55] text-white/85'
            : 'max-w-[100%] whitespace-pre-wrap text-[15px] leading-[1.65] text-white/85'
        }
      >
        {message.content}
        {streaming && !isUser && (
          <span className="ml-1 inline-block h-[13px] w-[7px] translate-y-[2px] animate-pulse bg-[var(--app-accent,#8b5cf6)] align-baseline" />
        )}
        {streaming && !isUser && !message.content && (
          <span className="inline-flex items-center gap-2 text-[13px] text-white/40">
            <Loader2 size={12} className="animate-spin" />
            Thinking…
          </span>
        )}
        {message.is_error && (
          <span className="mt-1 block text-[12px] text-red-400/80">Something went wrong.</span>
        )}
      </div>
    </div>
  )
}
