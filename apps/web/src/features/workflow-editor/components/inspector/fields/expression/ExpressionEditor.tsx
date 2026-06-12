import { useEffect, useMemo, useRef } from 'react'
import { Sparkles, X } from 'lucide-react'
import { cn } from '@/lib/cn'

/**
 * In-line editor for JSONata expressions saved with a leading `=` prefix.
 *
 * The saved value always starts with `=`. The editor strips it for display
 * and re-applies it on every keystroke, so the stored shape never drifts.
 * Clicking the close button drops the `=` and writes back a plain string,
 * which transitions the field renderer out of expression mode.
 *
 * Syntax highlighting is intentionally minimal in PR6 — `$identifier`,
 * `$func()`, `"string"`, numbers, operators. Full Monaco / autocomplete
 * arrives in PR7.
 */
interface ExpressionEditorProps {
  value: string                       // includes the leading `=`
  onChange: (next: string) => void   // receives the new value including `=` or '' on exit
  placeholder?: string
  multiline?: boolean
  rows?: number
  disabled?: boolean
}

export function ExpressionEditor({
  value,
  onChange,
  placeholder,
  multiline,
  rows = 1,
  disabled,
}: ExpressionEditorProps) {
  const inner = value.startsWith('=') ? value.slice(1) : value
  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement | null>(null)

  // Auto-grow textarea height in multiline mode so users can see what they're
  // writing without scroll. Capped to keep the inspector usable on long
  // expressions.
  useEffect(() => {
    if (!multiline) return
    const el = inputRef.current as HTMLTextAreaElement | null
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [inner, multiline])

  const commit = (next: string) => onChange(`=${next}`)

  const exit = () => {
    // Drop the `=` and write back the bare value so the renderer swaps back
    // to a plain string input. The user keeps whatever they typed.
    onChange(inner)
  }

  const highlights = useMemo(() => buildHighlights(inner), [inner])

  const editorClass = cn(
    'w-full resize-none bg-transparent font-mono text-[12px] leading-[18px] text-text outline-none',
    'placeholder:text-text-faint',
    multiline ? 'min-h-[26px]' : 'h-[26px] truncate',
  )

  return (
    <div
      className={cn(
        'group relative flex items-stretch rounded-[7px] border border-accent/40 bg-accent/[0.06] transition-colors',
        'focus-within:border-accent/70 focus-within:bg-accent/[0.10]',
        disabled && 'opacity-60',
      )}
    >
      <div className="flex shrink-0 items-center gap-1 border-r border-accent/20 px-2 py-1">
        <Sparkles className="h-3 w-3 text-accent" />
        <span className="font-mono text-[10px] font-semibold uppercase tracking-wide text-accent">
          fx
        </span>
      </div>

      {/* The textarea sits on top of the highlight layer so the user types
          normal text while the colored tokens render behind. Both share the
          exact same padding + font so they overlap pixel-perfectly. */}
      <div className="relative min-w-0 flex-1 px-2 py-1">
        <pre
          aria-hidden
          className={cn(
            'pointer-events-none absolute inset-0 m-0 overflow-hidden whitespace-pre-wrap break-words px-2 py-1 font-mono text-[12px] leading-[18px]',
            multiline ? '' : 'whitespace-pre overflow-hidden',
          )}
        >
          {highlights}
          {/* trailing newline so the highlight layer keeps the textarea's
              final empty line in sync */}
          {'\n'}
        </pre>
        {multiline ? (
          <textarea
            ref={inputRef as React.RefObject<HTMLTextAreaElement>}
            value={inner}
            onChange={e => commit(e.target.value)}
            placeholder={placeholder ?? 'JSONata expression'}
            disabled={disabled}
            rows={rows}
            spellCheck={false}
            className={cn(editorClass, 'relative z-10 text-transparent caret-text')}
          />
        ) : (
          <input
            ref={inputRef as React.RefObject<HTMLInputElement>}
            type="text"
            value={inner}
            onChange={e => commit(e.target.value)}
            placeholder={placeholder ?? 'JSONata expression'}
            disabled={disabled}
            spellCheck={false}
            className={cn(editorClass, 'relative z-10 text-transparent caret-text')}
          />
        )}
      </div>

      <button
        type="button"
        onClick={exit}
        title="Exit expression mode"
        disabled={disabled}
        className="shrink-0 px-1.5 text-text-faint transition-colors hover:text-text"
      >
        <X className="h-3 w-3" />
      </button>
    </div>
  )
}

/**
 * Cheap tokeniser for JSONata source. Splits the string into spans with
 * semantic colour classes. Order matters — longer / more-specific patterns
 * are matched first.
 */
function buildHighlights(source: string): React.ReactNode[] {
  const tokens: { regex: RegExp; className: string }[] = [
    { regex: /\$[A-Za-z_][A-Za-z0-9_]*/g, className: 'text-accent' },        // $step / $sum
    { regex: /"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/g, className: 'text-ok' }, // strings
    { regex: /\b\d+(?:\.\d+)?\b/g, className: 'text-warn' },                  // numbers
    { regex: /[+\-*/%=!<>&|?:.()[\]{},]/g, className: 'text-text-mute' },     // operators
  ]

  type Range = { start: number; end: number; className: string }
  const ranges: Range[] = []
  for (const { regex, className } of tokens) {
    let m: RegExpExecArray | null
    regex.lastIndex = 0
    while ((m = regex.exec(source)) !== null) {
      const start = m.index
      const end = start + m[0].length
      // Skip ranges that overlap an earlier (higher-priority) match.
      if (ranges.some(r => start < r.end && end > r.start)) continue
      ranges.push({ start, end, className })
    }
  }
  ranges.sort((a, b) => a.start - b.start)

  const out: React.ReactNode[] = []
  let cursor = 0
  ranges.forEach((r, i) => {
    if (cursor < r.start) out.push(source.slice(cursor, r.start))
    out.push(
      <span key={i} className={r.className}>
        {source.slice(r.start, r.end)}
      </span>,
    )
    cursor = r.end
  })
  if (cursor < source.length) out.push(source.slice(cursor))
  return out
}
