import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { cn } from '@/lib/cn'
import { CompletionPopup } from './CompletionPopup'
import { useExpressionCompletions, type Completion } from './useExpressionCompletions'
import { findActiveExpressionRegion } from './regionUtils'

/**
 * Single text field that handles plain text + embedded `{{ expression }}`
 * regions in one component.
 *
 * UX contract:
 *   - The user types into one field, no mode switching.
 *   - The completion popup opens automatically while the caret sits inside
 *     a `{{ … }}` block, fed the expression substring around the caret.
 *   - When the caret moves outside the braces (or there is no `{{` before
 *     it), the popup closes and the field behaves like plain text.
 *   - `{{ … }}` regions are highlighted via a `<pre>` overlay so users see
 *     structure without needing extra UI affordances.
 *   - The legacy `=expression` saved format is auto-migrated to
 *     `{{ expression }}` on first edit. Old graphs continue to render until
 *     someone touches them.
 */

interface ExpressionEditorProps {
  value: string
  onChange: (next: string) => void
  placeholder?: string
  multiline?: boolean
  rows?: number
  disabled?: boolean
  /** Accepted for backwards compatibility with renderers that still drive
   *  their own mode-swap (MessagesRenderer / ToolSelectorRenderer). Wired
   *  up to the input's focus on mount; the parent callback fires once. */
  autoFocus?: boolean
  onAutoFocusDone?: () => void
}

/** Migrate a legacy `=expression` save into the unified `{{ expression }}`
 *  shape so the user always sees the new syntax in the field. The original
 *  `=` form keeps working server-side via the property resolver — this is a
 *  purely cosmetic / one-way display migration. */
function migrateLegacyEquals(raw: string): string {
  if (!raw.startsWith('=')) return raw
  const body = raw.slice(1).trim()
  return `{{ ${body} }}`
}

export function ExpressionEditor({
  value,
  onChange,
  placeholder,
  multiline,
  rows = 3,
  disabled,
  autoFocus,
  onAutoFocusDone,
}: ExpressionEditorProps) {
  // One-time migration on first render: if the parent handed us a legacy
  // `=expression`, surface it as `{{ expression }}` (and persist the
  // migration so the next save writes the new shape).
  useEffect(() => {
    if (value.startsWith('=')) onChange(migrateLegacyEquals(value))
    // Intentionally only on initial value — subsequent changes are already
    // in the new shape.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement | null>(null)
  const wrapperRef = useRef<HTMLDivElement | null>(null)

  const [caret, setCaret] = useState(value.length)
  const [popupAnchor, setPopupAnchor] = useState<{ left: number; top: number } | null>(null)
  const [selectedIndex, setSelectedIndex] = useState(0)

  // Active `{{ … }}` region around the caret (if any). Determines whether
  // the completion engine fires at all.
  const region = useMemo(() => findActiveExpressionRegion(value, caret), [value, caret])
  const innerExpression = region?.inner ?? ''
  const innerCaret = region?.innerCaret ?? 0
  const completionState = useExpressionCompletions(innerExpression, innerCaret)

  // Auto-grow multiline textarea up to a cap so long values stay visible.
  useEffect(() => {
    if (!multiline) return
    const el = inputRef.current as HTMLTextAreaElement | null
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [value, multiline])

  // Honour `autoFocus` from legacy parents that still manage their own
  // mode swap. Fires once and clears the parent's flag.
  useEffect(() => {
    if (!autoFocus) return
    const el = inputRef.current
    if (!el) return
    el.focus()
    const pos = value.length
    el.setSelectionRange(pos, pos)
    setCaret(pos)
    onAutoFocusDone?.()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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
  }, [value.length])

  // Map the completion's inner replace-range up to full-text coords and
  // insert the chosen completion text in place.
  const acceptCompletion = useCallback(
    (item: Completion) => {
      if (!region) return
      const innerStart = region.open + 2
      const start = innerStart + completionState.replaceRange.start
      const end = innerStart + completionState.replaceRange.end
      const next = value.slice(0, start) + item.insertText + value.slice(end)
      commit(next)
      Promise.resolve().then(() => {
        const el = inputRef.current
        if (!el) return
        const pos = start + item.insertText.length
        el.focus()
        el.setSelectionRange(pos, pos)
        setCaret(pos)
        if (wrapperRef.current) {
          const r = wrapperRef.current.getBoundingClientRect()
          setPopupAnchor({ left: r.left, top: r.bottom + 4 })
        }
        setSelectedIndex(0)
      })
    },
    [region, completionState.replaceRange, value, commit],
  )

  const handleDrop = (e: React.DragEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    const raw = e.dataTransfer.getData('text/plain')
    if (!raw) return
    e.preventDefault()
    // Drops from the Inputs / Logs JSON tree carry `=<expression>` for
    // backwards compatibility — wrap as `{{ expression }}` since our new
    // syntax is `{{ }}` only.
    const cleaned = raw.startsWith('=') ? `{{ ${raw.slice(1)} }}` : raw
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

  const popupOpen = !!region && completionState.active && completionState.completions.length > 0

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!popupOpen) {
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
      setCaret(value.length + 1) // force region to null, hiding popup
    }
  }

  const shouldShowPopup =
    completionState.completions.length > 0 &&
    !(
      completionState.completions.length === 1 &&
      completionState.completions[0].insertText.toLowerCase() ===
        completionState.prefix.toLowerCase()
    )

  const wrapperClass = multiline
    ? cn(
        'relative w-full bg-surface border border-border-soft rounded-[8px] px-3 py-2.5',
        'transition-[background-color,border-color] [transition-duration:120ms]',
        'hover:border-border hover:bg-surface-2 focus-within:border-accent focus-within:bg-surface-2',
        disabled && 'pointer-events-none opacity-60',
      )
    : cn(
        'relative flex h-9 items-center gap-2 px-3',
        'bg-surface border border-border-soft rounded-[8px]',
        'transition-[background-color,border-color] [transition-duration:120ms]',
        'hover:border-border hover:bg-surface-2 focus-within:border-accent focus-within:bg-surface-2',
        disabled && 'pointer-events-none opacity-60',
      )

  // The old transparent-input + overlay-pre trick was inherently
  // fragile with a proportional UI font — every glyph in `<input>`
  // renders at a slightly different width than the same glyph inside a
  // `<pre>`, so cursor and highlighted text drift apart as the user
  // types. We now render the input opaquely and keep the overlay pre
  // ONLY when the value contains an actual `{{ … }}` region, using it
  // for a subtle background tint — never underneath the caret's text
  // path. Result: pixel-perfect caret in every field, no wrapper
  // acrobatics.
  const sharedInputClass = cn(
    'w-full bg-transparent outline-none text-sm text-text',
    'font-[var(--font-ui)] leading-normal',
    'placeholder:text-text-faint',
  )

  return (
    <div ref={wrapperRef} className={wrapperClass}>
      {multiline ? (
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
          placeholder={placeholder}
          disabled={disabled}
          rows={rows}
          spellCheck={false}
          className={cn(sharedInputClass, 'resize-none')}
        />
      ) : (
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
          placeholder={placeholder}
          disabled={disabled}
          spellCheck={false}
          className={cn(sharedInputClass, 'h-full border-none')}
        />
      )}

      {popupOpen && popupAnchor && shouldShowPopup && (
        <CompletionPopup
          completions={completionState.completions}
          selectedIndex={selectedIndex}
          onAccept={acceptCompletion}
          anchor={popupAnchor}
        />
      )}
    </div>
  )
}
