import { Send, Sparkles, Zap } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useCopilotChat } from '../../../hooks/useCopilotChat'

function TypingDots() {
  return (
    <span className="flex items-center gap-1 py-0.5">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-[var(--text-faint)]"
          style={{ animation: `copilot-bounce 1.2s infinite ease-in-out ${i * 0.15}s` }}
        />
      ))}
    </span>
  )
}

export function CopilotPanel() {
  const {
    msgs, input, setInput, busy,
    slashOpen, slashIdx, setSlashIdx, slashFilter,
    streamRef, inputRef,
    quickActions, send, onKeyDown, selectSlashCommand,
  } = useCopilotChat()

  return (
    <>
      <style>{`
        @keyframes copilot-bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40%            { transform: scale(1);   opacity: 1;   }
        }
      `}</style>

      <div className="flex h-full flex-col overflow-hidden">
        {/* Message stream */}
        <div
          ref={streamRef}
          className="min-h-0 flex-1 overflow-y-auto px-4 py-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          <div className="flex flex-col gap-3">
            {msgs.map((m, i) => (
              <div key={i} className={cn('flex max-w-full gap-2', m.role === 'user' ? 'justify-end' : 'items-start')}>
                {m.role === 'assistant' && (
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--surface-2)]">
                    <Sparkles className="h-3 w-3 text-[var(--text-mute)]" />
                  </span>
                )}
                <div className={cn(
                  'max-w-[85%] rounded-[10px] px-3 py-2 text-[12.5px] leading-relaxed',
                  m.role === 'assistant' ? 'bg-[var(--surface)] text-[var(--text)]' : 'bg-[var(--text)] text-[var(--bg)]',
                )}>
                  {m.content}
                </div>
              </div>
            ))}

            {busy && (
              <div className="flex items-start gap-2">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--surface-2)]">
                  <Sparkles className="h-3 w-3 text-[var(--text-mute)]" />
                </span>
                <div className="rounded-[10px] bg-[var(--surface)] px-3 py-2">
                  <TypingDots />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick action chips */}
        <div className="flex shrink-0 flex-wrap gap-1.5 px-4 pb-3">
          {quickActions.map(qa => (
            <button
              key={qa.text}
              disabled={busy}
              onClick={() => void send(qa.text)}
              className={cn(
                'flex items-center gap-1 rounded-full border border-[var(--border-faint)] px-2.5 py-1 text-[11.5px] text-[var(--text-mute)]',
                'transition-colors hover:border-[var(--border-soft)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
                'disabled:pointer-events-none disabled:opacity-40',
              )}
            >
              <Zap className="h-3 w-3" />
              {qa.label}
            </button>
          ))}
        </div>

        {/* Composer */}
        <div className="shrink-0 border-t border-[var(--border-faint)] p-3">
          <div className="relative">
            {slashOpen && slashFilter.length > 0 && (
              <div className="absolute bottom-[calc(100%+6px)] left-0 right-0 overflow-hidden rounded-[10px] border border-[var(--border)] bg-[var(--bg-2)] shadow-lg">
                {slashFilter.map((c, i) => (
                  <button
                    key={c.cmd}
                    onMouseEnter={() => setSlashIdx(i)}
                    onClick={() => selectSlashCommand(c.cmd)}
                    className={cn(
                      'flex w-full items-center gap-2.5 px-3 py-2 text-left text-[12px] transition-colors',
                      i === slashIdx ? 'bg-[var(--surface)]' : 'hover:bg-[var(--surface)]',
                    )}
                  >
                    <c.Icon className="h-3.5 w-3.5 shrink-0 text-[var(--text-faint)]" />
                    <span className="font-mono text-[var(--text)]">{c.cmd}</span>
                    <span className="text-[var(--text-faint)]">{c.hint}</span>
                  </button>
                ))}
              </div>
            )}

            <div className="flex items-end gap-2 rounded-[10px] border border-[var(--border-faint)] bg-[var(--bg)] px-3 py-2 transition-colors focus-within:border-[var(--border-soft)]">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask anything, or type / for commands…"
                rows={1}
                disabled={busy}
                className={cn(
                  'min-h-[20px] max-h-[120px] flex-1 resize-none bg-transparent text-[12.5px] leading-relaxed text-[var(--text)] outline-none',
                  'placeholder:text-[var(--text-dim)] disabled:opacity-50',
                  '[scrollbar-width:none] [&::-webkit-scrollbar]:hidden',
                )}
                style={{ height: 'auto' }}
                onInput={e => {
                  const el = e.currentTarget
                  el.style.height = 'auto'
                  el.style.height = `${el.scrollHeight}px`
                }}
              />
              <button
                disabled={busy || !input.trim()}
                onClick={() => void send()}
                className={cn(
                  'flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] bg-[var(--text)] text-[var(--bg)] transition-colors',
                  'hover:opacity-90 disabled:pointer-events-none disabled:opacity-30',
                )}
              >
                <Send className="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
