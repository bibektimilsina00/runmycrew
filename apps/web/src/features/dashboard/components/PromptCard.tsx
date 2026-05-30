import { useState, type KeyboardEvent } from 'react'
import { Mic, ArrowUp, Loader2, X } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useVoiceInput } from '@/shared/hooks/useVoiceInput'

interface PromptCardProps {
  prompt: string
  onPromptChange: (next: string) => void
  onSubmit: () => void
  busy?: boolean
  statusMessage?: string
  onCancel?: () => void
  placeholder?: string
}

/**
 * Controlled prompt card (Stitch-inspired): gradient border on focus / busy,
 * generous textarea, footer swaps to a status row while busy.
 */
export function PromptCard({
  prompt,
  onPromptChange,
  onSubmit,
  busy = false,
  statusMessage,
  onCancel,
  placeholder = 'What workflow shall we automate?',
}: PromptCardProps) {
  const [focused, setFocused] = useState(false)
  const voice = useVoiceInput({ value: prompt, onChange: onPromptChange })

  const handleSend = () => {
    if (!prompt.trim() || busy) return
    onSubmit()
  }

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div
      className={cn(
        'rounded-[16px] p-px transition-all duration-200',
        focused || busy
          ? 'bg-gradient-to-br from-[var(--accent)] via-[var(--accent-line)] to-[var(--accent-soft)]'
          : 'bg-[var(--border-faint)]',
      )}
    >
      <div className="rounded-[15px] bg-[var(--bg)] px-5 pt-5 pb-3">
        <textarea
          value={prompt}
          onChange={e => onPromptChange(e.target.value)}
          onKeyDown={onKey}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          disabled={busy}
          rows={5}
          placeholder={placeholder}
          className="block min-h-[120px] w-full resize-none border-none bg-transparent text-[15px] leading-[1.55] text-[var(--text)] outline-none placeholder:text-[var(--text-faint)] disabled:opacity-70"
        />

        <div className="mt-2 flex items-center justify-between gap-2">
          {busy ? (
            <div className="flex w-full items-center gap-2">
              <Loader2 className="h-3.5 w-3.5 animate-spin text-[var(--accent)]" />
              <span className="flex-1 text-[12.5px] text-[var(--text-mute)]">
                {statusMessage ?? 'Working…'}
              </span>
              {onCancel && (
                <button
                  onClick={onCancel}
                  title="Cancel"
                  className="inline-flex h-7 items-center gap-1 rounded-[7px] px-2 text-[11.5px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
                >
                  <X className="h-3 w-3" /> Cancel
                </button>
              )}
            </div>
          ) : (
            <>
              <span className="select-none text-[11px] text-[var(--text-faint)]">
                <kbd className="rounded border border-[var(--border-faint)] bg-[var(--surface)] px-1 py-px font-mono text-[10px]">
                  ↵
                </kbd>{' '}
                send ·{' '}
                <kbd className="rounded border border-[var(--border-faint)] bg-[var(--surface)] px-1 py-px font-mono text-[10px]">
                  ⇧↵
                </kbd>{' '}
                new line
              </span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={voice.toggle}
                  disabled={!voice.supported}
                  title={
                    voice.supported
                      ? voice.listening
                        ? 'Stop dictation'
                        : 'Dictate'
                      : 'Voice not supported in this browser'
                  }
                  className={cn(
                    'inline-flex h-8 w-8 items-center justify-center rounded-full transition-colors',
                    voice.listening
                      ? 'animate-pulse bg-[var(--err)]/15 text-[var(--err)]'
                      : 'text-[var(--text-mute)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
                    !voice.supported && 'cursor-not-allowed opacity-40',
                  )}
                >
                  <Mic className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={!prompt.trim()}
                  title="Send to Copilot"
                  className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[var(--text)] text-[var(--bg)] transition-all duration-150 hover:-translate-y-px hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:translate-y-0"
                >
                  <ArrowUp className="h-4 w-4" />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
