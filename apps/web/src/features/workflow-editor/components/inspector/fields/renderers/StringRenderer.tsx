import { useEffect, useRef, useState } from 'react'
import { Input, Textarea } from '@/shared/components'
import { cn } from '@/lib/cn'
import type { RendererProps } from '../types'
import { ExpressionEditor } from '../expression/ExpressionEditor'

/**
 * Plain-text + JSONata expression dual-mode field.
 *
 * The mode is encoded in the saved value itself: a leading `=` puts the
 * field into expression mode and routes evaluation through the JSONata
 * resolver at runtime (PR5). Bare strings stay literal.
 *
 * The mode-switch button is a small `fx` text badge in the label row to the
 * right — readable as "switch to expression", not as "AI generate" the way
 * the Sparkles icon read. No separate UI state for the mode itself; the rule
 * "string starts with `=` → expression" lives in one place and survives
 * reload, copy-paste, and undo/redo.
 */
export function StringRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const str = value === undefined || value === null ? '' : String(value)
  const opts = prop.typeOptions ?? {}
  const multiline = Boolean(opts.multiline)
  const rows = typeof opts.rows === 'number' ? opts.rows : 3
  const isExpression = str.startsWith('=')

  // Flags drive focus preservation across the plain ↔ expression renderer
  // swap. Without these, the unmounted `<input>` drops focus to `<body>` and
  // the next keypress (a held backspace, say) hits the global editor
  // shortcut and deletes the *selected node* instead of editing the field.
  const [autoFocusOnEnter, setAutoFocusOnEnter] = useState(false)
  const [autoFocusOnExit, setAutoFocusOnExit] = useState(false)
  const plainFieldRef = usePlainFieldFocusOnExit(autoFocusOnExit, () =>
    setAutoFocusOnExit(false),
  )

  if (isExpression) {
    // While in expression mode, intercept onChange so we can detect the
    // moment the user deletes back past the `=` and arm the plain-input
    // refocus on the next render.
    const handleExpressionChange = (next: string) => {
      if (!next.startsWith('=') && str.startsWith('=')) {
        setAutoFocusOnExit(true)
      }
      onChange(next)
    }
    return (
      <ExpressionEditor
        value={str}
        onChange={handleExpressionChange}
        placeholder={prop.placeholder}
        multiline={multiline}
        rows={rows}
        disabled={disabled}
        autoFocus={autoFocusOnEnter}
        onAutoFocusDone={() => setAutoFocusOnEnter(false)}
      />
    )
  }

  const enterExpressionMode = () => {
    setAutoFocusOnEnter(true)
    onChange(`=${str}`)
  }

  // Auto-promote to expression mode when the user types `=` or `$` as the
  // first character. Typing `=` is the canonical entry; typing `$` is the
  // shortcut (the renderer prefixes the saved value with `=` so the
  // dispatcher contract holds). Either transition stamps `autoFocusOnEnter`
  // so the ExpressionEditor that mounts next grabs focus.
  const handleTyped = (next: string) => {
    const enteringExpression =
      !str.startsWith('=') && (next.startsWith('=') || next.startsWith('$'))
    if (enteringExpression) setAutoFocusOnEnter(true)
    if (next.startsWith('$') && !str.startsWith('=')) {
      onChange(`=${next}`)
      return
    }
    onChange(next)
  }

  if (multiline) {
    return (
      <div className="relative">
        <Textarea
          ref={plainFieldRef as React.Ref<HTMLTextAreaElement>}
          value={str}
          onChange={e => handleTyped(e.target.value)}
          rows={rows}
          placeholder={prop.placeholder}
          disabled={disabled}
          className="rounded-[5px] text-[12px] leading-relaxed"
        />
        <FxBadge onClick={enterExpressionMode} disabled={disabled} />
      </div>
    )
  }

  return (
    <div className="relative">
      <Input
        ref={plainFieldRef as React.Ref<HTMLInputElement>}
        type={opts.password ? 'password' : 'text'}
        value={str}
        onChange={e => handleTyped(e.target.value)}
        placeholder={prop.placeholder}
        disabled={disabled}
        className="h-8 rounded-[5px] text-[12px]"
      />
      <FxBadge onClick={enterExpressionMode} disabled={disabled} />
    </div>
  )
}

type PlainField = HTMLInputElement | HTMLTextAreaElement

/**
 * Callback ref that focuses the plain input/textarea once when the parent
 * flag flips true (i.e. the renderer just swapped back from expression
 * mode). Clears the flag after focusing so subsequent renders don't yank
 * focus away from later edits.
 *
 * Called unconditionally at the top of `StringRenderer` (which is why it
 * works for either the input or the textarea branch) — switching variants
 * mid-render would otherwise violate the rules-of-hooks ordering rule.
 */
function usePlainFieldFocusOnExit(shouldFocus: boolean, onDone: () => void) {
  const ref = useRef<PlainField | null>(null)
  useEffect(() => {
    if (!shouldFocus) return
    const el = ref.current
    if (!el) return
    el.focus()
    // Place caret at end so continued typing appends to whatever was left
    // behind when the user shrank the expression past its `=`.
    const pos = el.value.length
    el.setSelectionRange(pos, pos)
    onDone()
  }, [shouldFocus, onDone])
  return (node: PlainField | null) => {
    ref.current = node
  }
}

interface FxBadgeProps {
  onClick: () => void
  disabled?: boolean
}

/**
 * Small monospace `fx` badge sitting on the label row, right-aligned above
 * the input. Click switches to expression mode.
 */
function FxBadge({ onClick, disabled }: FxBadgeProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title="Switch to expression (JSONata)"
      // FieldWrapper draws the label with `gap-1.5` (6px) below; the input
      // top is at y=0 in this `relative` wrapper, so -22px lands the badge
      // roughly on the label's baseline.
      className={cn(
        'absolute -top-[22px] right-0 flex h-[16px] items-center rounded-[3px] px-1.5',
        'font-mono text-[10px] font-semibold uppercase tracking-wide leading-none',
        'text-text-faint transition-colors hover:bg-accent/15 hover:text-accent',
        disabled && 'pointer-events-none opacity-50',
      )}
    >
      fx
    </button>
  )
}
