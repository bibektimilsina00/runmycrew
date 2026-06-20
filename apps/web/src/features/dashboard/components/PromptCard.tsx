import { useState, type KeyboardEvent } from 'react'
import { Mic, ArrowUp, Loader2, X, ChevronDown, Paperclip, LayoutGrid, Sparkles } from 'lucide-react'
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
        'border rounded-[12px] overflow-hidden bg-[var(--surface)] transition-colors',
        focused || busy ? 'border-[var(--accent-line)]' : 'border-[var(--border-soft)]',
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-[9px] px-[20px] py-[14px]">
        <span className="w-[24px] h-[24px] rounded-[7px] bg-[var(--accent-soft)] text-[var(--accent)] inline-flex items-center justify-center shrink-0">
          <Sparkles className="w-[14px] h-[14px]" />
        </span>
        <span className="text-[13.5px] font-semibold text-[var(--text)]">Build with Fuse AI</span>
        <span className="ml-auto inline-flex items-center gap-[6px] text-[12px] font-medium text-[var(--text-mute)] border border-[var(--border-soft)] rounded-[7px] px-[9px] py-[4px] cursor-pointer transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]">
          <span className="w-[6px] h-[6px] rounded-full bg-[var(--ok)]" />
          Claude Sonnet
          <ChevronDown className="w-[12px] h-[12px]" />
        </span>
      </div>

      {/* Body */}
      <div className="px-[20px] pt-[18px] pb-[14px]">
        <textarea
          value={prompt}
          onChange={e => onPromptChange(e.target.value)}
          onKeyDown={onKey}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          disabled={busy}
          rows={2}
          placeholder={placeholder}
          className="block min-h-[50px] w-full resize-none border-none bg-transparent text-[15px] leading-[1.55] tracking-[-0.005em] text-[var(--text)] outline-none placeholder:text-[var(--text-dim)] disabled:opacity-70"
        />

        <div className="flex items-center justify-between mt-[14px] gap-2">
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
              <div className="flex items-center gap-[6px]">
                <button
                  type="button"
                  className="inline-flex items-center gap-[6px] py-[6px] px-[11px] rounded-[8px] border border-[var(--border-soft)] bg-transparent text-[var(--text-mute)] text-[12.5px] font-medium transition-colors hover:bg-[rgba(255,255,255,0.05)] hover:text-[var(--text)]"
                >
                  <Paperclip className="w-[14px] h-[14px]" /> Attach
                </button>
                <button
                  type="button"
                  className="inline-flex items-center gap-[6px] py-[6px] px-[11px] rounded-[8px] border border-[var(--border-soft)] bg-transparent text-[var(--text-mute)] text-[12.5px] font-medium transition-colors hover:bg-[rgba(255,255,255,0.05)] hover:text-[var(--text)]"
                >
                  <LayoutGrid className="w-[14px] h-[14px]" /> Browse apps
                </button>
              </div>

              <div className="flex items-center gap-[10px]">
                <span className="hidden sm:inline-flex items-center gap-[5px] text-[11.5px] text-[var(--text-dim)]">
                  <kbd className="kbd">↵</kbd> to send
                </span>
                <button
                  type="button"
                  onClick={voice.toggle}
                  disabled={!voice.supported}
                  title={voice.supported ? (voice.listening ? 'Stop dictation' : 'Dictate') : 'Voice not supported in this browser'}
                  className={cn(
                    'inline-flex w-[34px] h-[34px] items-center justify-center rounded-[9px] border border-[var(--border-soft)] bg-transparent transition-colors',
                    voice.listening
                      ? 'animate-pulse bg-[var(--err)]/15 text-[var(--err)] border-transparent'
                      : 'text-[var(--text-mute)] hover:bg-[rgba(255,255,255,0.06)] hover:text-[var(--text)]',
                    !voice.supported && 'cursor-not-allowed opacity-40',
                  )}
                >
                  <Mic className="h-[15px] w-[15px]" />
                </button>
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={!prompt.trim()}
                  title="Send to Copilot"
                  className="inline-flex w-[34px] h-[34px] items-center justify-center rounded-[9px] bg-[var(--accent)] text-white shadow-[0_4px_14px_var(--accent-soft)] transition-[filter] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-30"
                >
                  <ArrowUp className="h-[16px] w-[16px]" strokeWidth={2.2} />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
