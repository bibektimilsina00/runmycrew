import { useEffect, useRef } from 'react'
import { cn } from '@/lib/cn'
import type { Completion } from './useExpressionCompletions'

interface CompletionPopupProps {
  completions: Completion[]
  selectedIndex: number
  onAccept: (item: Completion) => void
  /** Anchor position in viewport pixels — top-left of the popup. */
  anchor: { left: number; top: number }
}

/**
 * Floating completion list for the expression editor. Keyboard navigation
 * (arrows / Tab / Enter / Esc) is owned by the parent ExpressionEditor —
 * this component only renders the list and reports clicks.
 *
 * The popup auto-scrolls to keep the active item in view as the parent
 * cycles through completions.
 */
export function CompletionPopup({
  completions,
  selectedIndex,
  onAccept,
  anchor,
}: CompletionPopupProps) {
  const listRef = useRef<HTMLDivElement>(null)
  const activeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: 'nearest' })
  }, [selectedIndex])

  if (completions.length === 0) return null

  return (
    <div
      ref={listRef}
      className="fixed z-50 max-h-[260px] w-[280px] overflow-y-auto rounded-[8px] border border-border shadow-[0_12px_32px_-8px_oklch(0_0_0/0.55)] backdrop-blur-md"
      style={{
        left: anchor.left,
        top: anchor.top,
        // Explicit opaque fill so the popup never bleeds into whatever is
        // beneath the editor. `bg-bg-2` is too close to the inspector's own
        // surface and looked translucent against the dark canvas.
        backgroundColor: 'var(--surface-2)',
      }}
      onMouseDown={e => e.preventDefault()}  // keep editor focused on click
    >
      {completions.map((c, i) => {
        const active = i === selectedIndex
        return (
          <button
            key={`${c.kind}:${c.label}`}
            ref={active ? activeRef : undefined}
            type="button"
            // Click accepts. We intentionally do NOT sync selection on hover
            // — that fought the keyboard: arrow keys would change the index
            // and ghost text, but the popup highlight would snap back to
            // whatever item the cursor happened to be over. Keyboard owns
            // selectedIndex; hover is CSS-only visual feedback.
            onClick={() => onAccept(c)}
            // `bg-accent/12` Tailwind opacity modifier wasn't compiling in
            // this project's Tailwind config, so the active row had no
            // visible fill — keyboard selection looked broken even though
            // the state was correct. Use `color-mix(...)` inline style for
            // a fill that always renders.
            style={
              active
                ? {
                    backgroundColor:
                      'color-mix(in oklch, var(--accent) 22%, transparent)',
                  }
                : undefined
            }
            className={cn(
              'flex w-full items-start gap-2 border-l-2 px-2.5 py-1.5 text-left transition-colors',
              active
                ? 'border-accent text-text'
                : 'border-transparent text-text hover:bg-surface',
            )}
          >
            <KindBadge kind={c.kind} />
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline gap-2">
                <span className="truncate font-mono text-[12px] text-text">{c.label}</span>
                {c.detail && (
                  <span className="ml-auto shrink-0 font-mono text-[10px] text-text-faint">
                    {c.detail}
                  </span>
                )}
              </div>
              {c.description && (
                <div className="truncate text-[11px] text-text-faint">{c.description}</div>
              )}
            </div>
          </button>
        )
      })}
    </div>
  )
}

const BADGE_CLASS: Record<Completion['kind'], string> = {
  variable: 'bg-[rgba(125,207,255,0.14)] text-[#7dcfff]',
  function: 'bg-[rgba(187,154,247,0.16)] text-[#bb9af7]',
  field:    'bg-[rgba(158,206,106,0.16)] text-[#9ece6a]',
  node:     'bg-[rgba(224,175,104,0.16)] text-[#e0af68]',
}

const BADGE_LABEL: Record<Completion['kind'], string> = {
  variable: 'var',
  function: 'fn',
  field:    'f',
  node:     'n',
}

function KindBadge({ kind }: { kind: Completion['kind'] }) {
  return (
    <span
      className={cn(
        'mt-0.5 inline-flex h-[16px] w-[18px] shrink-0 items-center justify-center rounded-[3px] font-mono text-[9.5px] font-semibold uppercase leading-none',
        BADGE_CLASS[kind],
      )}
    >
      {BADGE_LABEL[kind]}
    </span>
  )
}
