import { useEffect, useMemo, useRef } from 'react'
import { cn } from '@/lib/cn'
import type { Completion } from './useExpressionCompletions'

interface CompletionPopupProps {
  completions: Completion[]
  selectedIndex: number
  onAccept: (item: Completion) => void
  /** Anchor position in viewport pixels — top-left of the popup. */
  anchor: { left: number; top: number }
  /** Substring under the caret being filtered — used to highlight the
   *  matched fragment inside each label. */
  prefix?: string
}

/**
 * Floating completion widget for the expression editor.
 *
 * Layout follows the pattern users know from VSCode / Retool:
 *   1. Grouped list on top — one sticky header per kind (functions,
 *      variables, node outputs, …). Each row: a coloured kind icon, the
 *      label (with the currently-typed prefix highlighted), and the
 *      right-aligned type signature.
 *   2. Docs preview beneath the selected row — pulls `description` from
 *      the completion. Hidden when the row has no description.
 *   3. Keyboard hint footer — ↑↓/↵/Esc.
 *
 * Keyboard navigation stays owned by the parent `ExpressionEditor`; this
 * component only renders and reports clicks / hover.
 */
export function CompletionPopup({
  completions,
  selectedIndex,
  onAccept,
  anchor,
  prefix = '',
}: CompletionPopupProps) {
  const listRef = useRef<HTMLDivElement>(null)
  const activeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: 'nearest' })
  }, [selectedIndex])

  // Group completions by kind while preserving parent order. This is
  // stable — the parent already sorts by relevance within each kind, so
  // we only need to bucket them here.
  const groups = useMemo(() => {
    const map = new Map<Completion['kind'], { items: Completion[]; startIndex: number }>()
    completions.forEach((c, i) => {
      const g = map.get(c.kind)
      if (g) g.items.push(c)
      else map.set(c.kind, { items: [c], startIndex: i })
    })
    return Array.from(map.entries()).map(([kind, g]) => ({ kind, ...g }))
  }, [completions])

  const selected = completions[selectedIndex]

  if (completions.length === 0) return null

  return (
    <div
      ref={listRef}
      className={cn(
        'fixed z-50 flex w-[340px] flex-col overflow-hidden rounded-[10px]',
        'border border-border shadow-[0_20px_48px_-12px_oklch(0_0_0/0.65)]',
        'backdrop-blur-md',
      )}
      style={{
        left: anchor.left,
        top: anchor.top,
        backgroundColor: 'var(--bg-2)',
        maxHeight: 'min(420px, 80vh)',
      }}
      onMouseDown={e => e.preventDefault()}
    >
      {/* Group + row list */}
      <div className="min-h-0 flex-1 overflow-y-auto py-1">
        {groups.map(g => (
          <div key={g.kind}>
            <div className="sticky top-0 z-[1] bg-[var(--bg-2)] px-3 pb-1 pt-2 text-[9.5px] font-semibold uppercase tracking-widest text-[var(--text-dim)]">
              {KIND_HEADER[g.kind]}
              <span className="ml-1.5 text-[var(--text-faint)] normal-case tracking-normal">({g.items.length})</span>
            </div>
            {g.items.map((c, iInGroup) => {
              const globalIndex = g.startIndex + iInGroup
              const active = globalIndex === selectedIndex
              return (
                <button
                  key={`${c.kind}:${c.label}:${globalIndex}`}
                  ref={active ? activeRef : undefined}
                  type="button"
                  onClick={() => onAccept(c)}
                  className={cn(
                    'group flex w-full items-center gap-2.5 px-2.5 py-1.5 text-left transition-colors',
                    active
                      ? 'bg-[color-mix(in_oklab,var(--accent)_18%,transparent)] text-text'
                      : 'text-text hover:bg-[var(--surface)]',
                  )}
                >
                  <KindIcon kind={c.kind} />
                  <span className="min-w-0 flex-1 truncate font-mono text-[12.5px]">
                    <HighlightedLabel label={c.label} prefix={prefix} />
                  </span>
                  {c.detail && (
                    <span
                      className={cn(
                        'shrink-0 font-mono text-[10.5px]',
                        active ? 'text-[var(--text-mute)]' : 'text-[var(--text-faint)]',
                      )}
                    >
                      {c.detail}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        ))}
      </div>

      {/* Docs preview — only when the selected row carries a description */}
      {selected?.description && (
        <div className="shrink-0 border-t border-[var(--border-faint)] bg-[var(--surface)] px-3 py-2">
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-[11.5px] font-semibold text-[var(--text)]">
              {selected.label}
            </span>
            {selected.detail && (
              <span className="font-mono text-[10.5px] text-[var(--text-faint)]">
                {selected.detail}
              </span>
            )}
          </div>
          <p className="mt-0.5 text-[11.5px] leading-[1.4] text-[var(--text-mute)]">
            {selected.description}
          </p>
        </div>
      )}

      {/* Keyboard hint footer */}
      <div className="shrink-0 border-t border-[var(--border-faint)] bg-[var(--bg)] px-3 py-1.5">
        <div className="flex items-center gap-3 text-[10px] text-[var(--text-faint)]">
          <span><Kbd>↑</Kbd><Kbd>↓</Kbd> Navigate</span>
          <span><Kbd>↵</Kbd> Insert</span>
          <span><Kbd>Tab</Kbd> Accept</span>
          <span className="ml-auto"><Kbd>Esc</Kbd> Close</span>
        </div>
      </div>
    </div>
  )
}

const KIND_HEADER: Record<Completion['kind'], string> = {
  function: 'Functions',
  variable: 'Variables',
  field:    'Fields',
  node:     'Node Outputs',
}

const KIND_ICON_CLASS: Record<Completion['kind'], string> = {
  function: 'bg-[rgba(187,154,247,0.16)] text-[#bb9af7]',
  variable: 'bg-[rgba(125,207,255,0.16)] text-[#7dcfff]',
  field:    'bg-[rgba(158,206,106,0.16)] text-[#9ece6a]',
  node:     'bg-[rgba(224,175,104,0.16)] text-[#e0af68]',
}

function KindIcon({ kind }: { kind: Completion['kind'] }) {
  return (
    <span
      aria-hidden
      className={cn(
        'flex h-[20px] w-[24px] shrink-0 items-center justify-center rounded-[4px]',
        KIND_ICON_CLASS[kind],
      )}
    >
      {kind === 'function' && <FnGlyph />}
      {kind === 'variable' && <VarGlyph />}
      {kind === 'field' && <FieldGlyph />}
      {kind === 'node' && <NodeGlyph />}
    </span>
  )
}

function FnGlyph() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
      <path d="M4 3v2.2c0 .6-.5 1.1-1.1 1.1H2M4 3h1.5c1 0 1.6.8 1.4 1.7l-1.5 8c-.2.9-.8 1.7-1.4 1.7H2M13 6.5H8.5m5.5 3H9" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  )
}

function VarGlyph() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
      <path d="M3 4l3.5 8L8 6l3 6 2-8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function FieldGlyph() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
      <rect x="2.5" y="3.5" width="11" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M6 7h4M6 10h3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  )
}

function NodeGlyph() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
      <rect x="2" y="5" width="5" height="6" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="9" y="2.5" width="5" height="4" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="9" y="9.5" width="5" height="4" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <path d="M7 8h1.5m0-3.5V8m0 0V11.5" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  )
}

/**
 * Highlight the currently-typed prefix inside a label. Case-insensitive
 * match; falls back to plain rendering when the prefix doesn't appear
 * as a leading substring (parent already filters, so this is rare — but
 * the label may prefix its trigger character, e.g. `$` on functions).
 */
function HighlightedLabel({ label, prefix }: { label: string; prefix: string }) {
  if (!prefix) return <>{label}</>
  const i = label.toLowerCase().indexOf(prefix.toLowerCase())
  if (i < 0) return <>{label}</>
  return (
    <>
      {i > 0 && <span className="text-[var(--text-mute)]">{label.slice(0, i)}</span>}
      <span className="font-semibold text-[var(--text)]">{label.slice(i, i + prefix.length)}</span>
      <span className="text-[var(--text-mute)]">{label.slice(i + prefix.length)}</span>
    </>
  )
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="mx-0.5 inline-flex min-w-[16px] items-center justify-center rounded-[3px] border border-[var(--border-faint)] bg-[var(--surface)] px-1 py-[1px] font-mono text-[9.5px] text-[var(--text-mute)]">
      {children}
    </kbd>
  )
}
