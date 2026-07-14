import { useState, type KeyboardEvent } from 'react'
import { Mic, ArrowUp, Loader2, X, Workflow, Users } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useVoiceInput } from '@/shared/hooks/useVoiceInput'
import { Icons } from '@/shared/components/icons'

export type BuildKind = 'workflow' | 'crew'

interface PromptCardProps {
  prompt: string
  onPromptChange: (next: string) => void
  onSubmit: () => void
  busy?: boolean
  statusMessage?: string
  onCancel?: () => void
  placeholder?: string
  kind?: BuildKind
  onKindChange?: (k: BuildKind) => void
}

export function PromptCard({
  prompt,
  onPromptChange,
  onSubmit,
  busy = false,
  statusMessage,
  onCancel,
  placeholder = 'What workflow shall we automate?',
  kind = 'workflow',
  onKindChange,
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
        <span className="w-[26px] h-[26px] inline-flex items-center justify-center shrink-0 text-[var(--accent)]">
          <Icons.BrandMark className="w-[22px] h-[22px]" />
        </span>
        <span className="text-[13.5px] font-semibold text-[var(--text)]">Build with AI</span>
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
              {/* Build target: workflow or crew. Copilot builds either. */}
              <div className="inline-flex items-center rounded-[8px] border border-[var(--border-soft)] bg-[var(--surface-2)] p-[2px]">
                {(['workflow', 'crew'] as const).map(k => (
                  <button
                    key={k}
                    type="button"
                    onClick={() => onKindChange?.(k)}
                    className={cn(
                      'inline-flex items-center gap-[5px] rounded-[6px] px-[9px] py-[4px] text-[12px] font-medium capitalize transition-colors',
                      kind === k
                        ? 'bg-[var(--surface)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-soft)]'
                        : 'text-[var(--text-mute)] hover:text-[var(--text)]',
                    )}
                  >
                    {k === 'workflow' ? <Workflow className="h-[13px] w-[13px]" /> : <Users className="h-[13px] w-[13px]" />}
                    {k}
                  </button>
                ))}
              </div>
              <div className="ml-auto flex items-center gap-[10px]">
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
