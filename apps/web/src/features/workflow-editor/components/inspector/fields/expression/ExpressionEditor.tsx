import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { cn } from '@/lib/cn'
import { CompletionPopup } from './CompletionPopup'
import { useExpressionCompletions, type Completion } from './useExpressionCompletions'

/**
 * In-line editor for JSONata expressions saved with a leading `=` prefix.
 *
 * Visual chrome mirrors the regular Input / Textarea components exactly —
 * same border, padding, height, hover / focus states. The only difference
 * is a transparent input layered over a `<pre>` that syntax-colours the
 * value, so users see structure without any extra UI noise (no fx pill,
 * no boxed accent border, no close button).
 *
 * The saved value always starts with `=`; the editor displays it verbatim.
 * When the user deletes the `=`, StringRenderer swaps the field back to a
 * plain Input on the next render, so no explicit "exit expression mode"
 * affordance is needed.
 */
interface ExpressionEditorProps {
  value: string                       // includes the leading `=`
  onChange: (next: string) => void
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
  rows = 3,
  disabled,
}: ExpressionEditorProps) {
  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement | null>(null)
  const wrapperRef = useRef<HTMLDivElement | null>(null)

  const [caret, setCaret] = useState(value.length)
  const [popupOpen, setPopupOpen] = useState(false)
  const [popupAnchor, setPopupAnchor] = useState<{ left: number; top: number } | null>(null)
  const [selectedIndex, setSelectedIndex] = useState(0)

  // Completion engine works on the expression body (without the leading `=`)
  // since the caret index inside `value` is offset by 1 from the body.
  const inner = value.startsWith('=') ? value.slice(1) : value
  const innerCaret = Math.max(0, caret - (value.startsWith('=') ? 1 : 0))
  const completionState = useExpressionCompletions(inner, innerCaret)

  // Auto-grow multiline textarea up to a cap so long expressions stay
  // visible without the rest of the inspector exploding.
  useEffect(() => {
    if (!multiline) return
    const el = inputRef.current as HTMLTextAreaElement | null
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [value, multiline])

  const commit = useCallback(
    (next: string) => {
      onChange(next)
      setSelectedIndex(0)
    },
    [onChange],
  )

  const syncCaret = useCallback(() => {
    const el = inputRef.current
    if (!el) return
    const pos = el.selectionStart ?? value.length
    setCaret(pos)
    if (wrapperRef.current) {
      const r = wrapperRef.current.getBoundingClientRect()
      setPopupAnchor({ left: r.left, top: r.bottom + 4 })
    }
    setPopupOpen(true)
  }, [value.length])

  const acceptCompletion = useCallback(
    (item: Completion) => {
      // ReplaceRange is in inner-string coords; lift to full-value coords.
      const offset = value.startsWith('=') ? 1 : 0
      const start = completionState.replaceRange.start + offset
      const end = completionState.replaceRange.end + offset
      const next = value.slice(0, start) + item.insertText + value.slice(end)
      commit(next)
      setPopupOpen(false)
      Promise.resolve().then(() => {
        const el = inputRef.current
        if (!el) return
        const pos = start + item.insertText.length
        el.focus()
        el.setSelectionRange(pos, pos)
        setCaret(pos)
      })
    },
    [completionState.replaceRange, value, commit],
  )

  const handleDrop = (e: React.DragEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    // Drops from the Inputs / Logs JSON tree carry `=<expression>` because
    // they're designed to drop on a plain text field that needs the `=` to
    // enter expression mode. We're already in expression mode — strip the
    // leading `=` so the result is `... $step.x ...`, not `... =$step.x ...`.
    const raw = e.dataTransfer.getData('text/plain')
    if (!raw) return
    e.preventDefault()
    const cleaned = raw.startsWith('=') ? raw.slice(1) : raw
    const el = e.currentTarget
    const start = el.selectionStart ?? value.length
    const end = el.selectionEnd ?? start
    const next = value.slice(0, start) + cleaned + value.slice(end)
    commit(next)
    Promise.resolve().then(() => {
      el.focus()
      const pos = start + cleaned.length
      el.setSelectionRange(pos, pos)
      setCaret(pos)
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!popupOpen || !completionState.active || completionState.completions.length === 0) {
      if (e.key === 'Escape') (e.target as HTMLElement).blur()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(i => (i + 1) % completionState.completions.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(
        i => (i - 1 + completionState.completions.length) % completionState.completions.length,
      )
    } else if (e.key === 'Enter' || e.key === 'Tab') {
      const item = completionState.completions[selectedIndex]
      if (item) {
        e.preventDefault()
        acceptCompletion(item)
      }
    } else if (e.key === 'Escape') {
      e.preventDefault()
      setPopupOpen(false)
    }
  }

  const highlights = useMemo(() => buildHighlights(value), [value])

  // Chrome that mirrors `Input` (single-line) or `Textarea` (multiline).
  // No accent tint, no `fx` pill, no exit button — the syntax colouring is
  // the only signal that we're in expression mode.
  const wrapperClass = multiline
    ? cn(
        'relative w-full bg-bg border border-border-faint rounded-[8px] px-3 py-2.5',
        'transition-[background-color,border-color] duration-[120ms]',
        'hover:border-border-soft focus-within:border-border focus-within:bg-surface',
        disabled && 'pointer-events-none opacity-60',
      )
    : cn(
        'relative flex h-9 items-center gap-2 px-3',
        'bg-bg border border-border-faint rounded-[8px]',
        'transition-[background-color,border-color] duration-[120ms]',
        'hover:border-border-soft focus-within:border-border focus-within:bg-surface',
        disabled && 'pointer-events-none opacity-60',
      )

  const sharedInputClass = cn(
    'w-full bg-transparent outline-none text-sm text-transparent caret-text',
    'placeholder:text-text-faint',
  )

  const sharedPreClass = cn(
    'pointer-events-none m-0 font-mono text-sm leading-normal whitespace-pre-wrap break-words',
  )

  return (
    <div ref={wrapperRef} className={wrapperClass}>
      {multiline ? (
        <div className="relative w-full">
          <pre aria-hidden className={cn(sharedPreClass, 'absolute inset-0')}>
            {highlights}
            {'\n'}
          </pre>
          <textarea
            ref={inputRef as React.RefObject<HTMLTextAreaElement>}
            value={value}
            onChange={e => {
              commit(e.target.value)
              syncCaret()
            }}
            onSelect={syncCaret}
            onClick={syncCaret}
            onKeyUp={syncCaret}
            onKeyDown={handleKeyDown}
            onDrop={handleDrop}
            onFocus={syncCaret}
            onBlur={() => setPopupOpen(false)}
            placeholder={placeholder ?? 'JSONata expression'}
            disabled={disabled}
            rows={rows}
            spellCheck={false}
            className={cn(sharedInputClass, 'relative z-10 resize-none font-mono')}
          />
        </div>
      ) : (
        <div className="relative h-full min-w-0 flex-1">
          <pre aria-hidden className={cn(sharedPreClass, 'absolute inset-0 flex items-center')}>
            {highlights}
          </pre>
          <input
            ref={inputRef as React.RefObject<HTMLInputElement>}
            type="text"
            value={value}
            onChange={e => {
              commit(e.target.value)
              syncCaret()
            }}
            onSelect={syncCaret}
            onClick={syncCaret}
            onKeyUp={syncCaret}
            onKeyDown={handleKeyDown}
            onDrop={handleDrop}
            onFocus={syncCaret}
            onBlur={() => setPopupOpen(false)}
            placeholder={placeholder ?? 'JSONata expression'}
            disabled={disabled}
            spellCheck={false}
            className={cn(sharedInputClass, 'relative z-10 h-full font-mono border-none')}
          />
        </div>
      )}

      {popupOpen && popupAnchor && completionState.active && (
        <CompletionPopup
          completions={completionState.completions}
          selectedIndex={selectedIndex}
          onSelectIndex={setSelectedIndex}
          onAccept={acceptCompletion}
          anchor={popupAnchor}
        />
      )}
    </div>
  )
}

/**
 * Cheap tokeniser for JSONata source. Splits the string into spans with
 * semantic colour classes. Order matters — longer / more-specific patterns
 * are matched first. The leading `=` (when present) is given its own dim
 * class so users see the mode marker without it dominating the value.
 */
function buildHighlights(source: string): React.ReactNode[] {
  // Tokenise the body (without the leading `=`) and prepend a dim `=` span
  // if the source is in expression mode.
  const equalsPrefix = source.startsWith('=')
  const body = equalsPrefix ? source.slice(1) : source

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
    while ((m = regex.exec(body)) !== null) {
      const start = m.index
      const end = start + m[0].length
      if (ranges.some(r => start < r.end && end > r.start)) continue
      ranges.push({ start, end, className })
    }
  }
  ranges.sort((a, b) => a.start - b.start)

  const out: React.ReactNode[] = []
  if (equalsPrefix) {
    out.push(
      <span key="eq" className="text-text-faint">
        =
      </span>,
    )
  }
  let cursor = 0
  ranges.forEach((r, i) => {
    if (cursor < r.start) out.push(body.slice(cursor, r.start))
    out.push(
      <span key={`t-${i}`} className={r.className}>
        {body.slice(r.start, r.end)}
      </span>,
    )
    cursor = r.end
  })
  if (cursor < body.length) out.push(body.slice(cursor))
  return out
}
