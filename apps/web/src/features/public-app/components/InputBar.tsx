import { useEffect, useRef } from 'react'
import { ArrowUp, StopCircle } from 'lucide-react'

interface InputBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  onCancel?: () => void
  disabled?: boolean
  isStreaming?: boolean
  placeholder?: string
}

/**
 * Auto-resizing textarea + send / stop button. ⌘↩ sends.
 */
export function InputBar({
  value,
  onChange,
  onSubmit,
  onCancel,
  disabled,
  isStreaming,
  placeholder,
}: InputBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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

  return (
    <div className="mx-auto flex w-full max-w-[860px] items-end gap-2 rounded-[16px] border border-white/10 bg-white/[0.04] px-3 py-2 shadow-[0_10px_40px_-12px_rgba(0,0,0,0.5)] focus-within:border-white/25">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={key}
        rows={1}
        placeholder={placeholder ?? 'Send a message… (⌘↩ to send)'}
        disabled={disabled}
        className="min-h-[24px] w-full resize-none bg-transparent px-1 py-1.5 text-[14.5px] leading-[1.5] text-white placeholder:text-white/30 focus:outline-none disabled:opacity-40"
      />
      {isStreaming ? (
        <button
          onClick={onCancel}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white transition hover:brightness-110"
          style={{ background: 'var(--app-accent, #8b5cf6)' }}
          title="Stop"
        >
          <StopCircle size={14} />
        </button>
      ) : (
        <button
          onClick={submit}
          disabled={!value.trim() || disabled}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
          style={{ background: 'var(--app-accent, #8b5cf6)' }}
          title="Send (⌘↩)"
        >
          <ArrowUp size={14} />
        </button>
      )}
    </div>
  )
}
