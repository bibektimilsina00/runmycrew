import { useEffect, useRef } from 'react'
import { ArrowUp, Paperclip, StopCircle, X } from 'lucide-react'

export interface AttachedFile {
  id: string
  url: string
  filename: string
  mime: string
  size_bytes: number
}

interface InputBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  onCancel?: () => void
  disabled?: boolean
  isStreaming?: boolean
  placeholder?: string
  allowFileUpload?: boolean
  attachments?: AttachedFile[]
  onAttach?: (file: File) => Promise<void> | void
  onRemoveAttachment?: (id: string) => void
  uploading?: boolean
}

/**
 * Auto-resizing textarea + attach + send/stop button.
 *
 * Accessibility:
 * - <form> wrapper for keyboard submit
 * - aria-label on all controls
 * - focus rings via `focus-visible:ring-2` follow the theme accent
 * - respects `prefers-reduced-motion`
 */
export function InputBar({
  value,
  onChange,
  onSubmit,
  onCancel,
  disabled,
  isStreaming,
  placeholder,
  allowFileUpload,
  attachments = [],
  onAttach,
  onRemoveAttachment,
  uploading,
}: InputBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(200, el.scrollHeight)}px`
  }, [value])

  const submit = () => {
    if (!value.trim() || disabled || isStreaming) return
    onSubmit()
  }

  const key = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      submit()
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const pick = () => fileRef.current?.click()
  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f || !onAttach) return
    await onAttach(f)
    e.target.value = ''
  }

  return (
    <div className="mx-auto flex w-full max-w-[860px] flex-col gap-1.5">
      {attachments.length > 0 && (
        <ul className="flex flex-wrap items-center gap-1.5" aria-label="Attached files">
          {attachments.map(a => (
            <li
              key={a.id}
              className="flex items-center gap-1.5 rounded-[7px] border border-white/10 bg-white/[0.04] px-2 py-1 text-[11.5px] text-white/80"
            >
              <span className="truncate max-w-[180px]">{a.filename}</span>
              {onRemoveAttachment && (
                <button
                  type="button"
                  onClick={() => onRemoveAttachment(a.id)}
                  className="rounded p-0.5 text-white/60 hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
                  aria-label={`Remove ${a.filename}`}
                >
                  <X size={11} />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      <form
        onSubmit={e => {
          e.preventDefault()
          submit()
        }}
        className="flex w-full items-end gap-2 rounded-[16px] border border-white/10 bg-white/[0.04] px-3 py-2 shadow-[0_10px_40px_-12px_rgba(0,0,0,0.5)] focus-within:border-white/25 motion-safe:transition-colors"
      >
        {allowFileUpload && (
          <>
            <input ref={fileRef} type="file" onChange={onFile} className="hidden" />
            <button
              type="button"
              onClick={pick}
              disabled={uploading || disabled}
              aria-label="Attach a file"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white/60 hover:bg-white/[0.06] hover:text-white disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/50"
            >
              <Paperclip size={14} />
            </button>
          </>
        )}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={key}
          rows={1}
          placeholder={placeholder ?? 'Send a message… (⌘↩ to send)'}
          disabled={disabled}
          aria-label="Message"
          className="min-h-[24px] w-full resize-none bg-transparent px-1 py-1.5 text-[14.5px] leading-[1.5] text-white placeholder:text-white/30 focus:outline-none disabled:opacity-40"
        />
        {isStreaming ? (
          <button
            type="button"
            onClick={onCancel}
            aria-label="Stop response"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white motion-safe:transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/50"
            style={{ background: 'var(--app-accent, #8b5cf6)' }}
            title="Stop"
          >
            <StopCircle size={14} />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!value.trim() || disabled}
            aria-label="Send message"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white motion-safe:transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/50"
            style={{ background: 'var(--app-accent, #8b5cf6)' }}
            title="Send (⌘↩)"
          >
            <ArrowUp size={14} />
          </button>
        )}
      </form>
    </div>
  )
}
