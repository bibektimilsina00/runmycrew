import { useState } from 'react'
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
 * The mode-switch button is a small `fx` text badge at the top-right corner
 * of the input — readable as "switch to expression", not as "AI generate"
 * the way the Sparkles icon read. No separate UI state for the mode itself;
 * the rule "string starts with `=` → expression" lives in one place and
 * survives reload, copy-paste, and undo/redo.
 */
export function StringRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const str = value === undefined || value === null ? '' : String(value)
  const opts = prop.typeOptions ?? {}
  const multiline = Boolean(opts.multiline)
  const rows = typeof opts.rows === 'number' ? opts.rows : 3
  const isExpression = str.startsWith('=')

  // Tracks whether the most recent mode change came from user action
  // (typing `=` / `$`, clicking the fx badge) so the ExpressionEditor that
  // mounts next knows to grab focus + restore the caret.
  const [autoFocusOnEnter, setAutoFocusOnEnter] = useState(false)

  if (isExpression) {
    return (
      <ExpressionEditor
        value={str}
        onChange={onChange}
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
          value={str}
          onChange={e => handleTyped(e.target.value)}
          rows={rows}
          placeholder={prop.placeholder}
          disabled={disabled}
          className="text-[12px] leading-relaxed"
        />
        <FxBadge onClick={enterExpressionMode} disabled={disabled} />
      </div>
    )
  }

  return (
    <div className="relative">
      <Input
        type={opts.password ? 'password' : 'text'}
        value={str}
        onChange={e => handleTyped(e.target.value)}
        placeholder={prop.placeholder}
        disabled={disabled}
        className="h-8 text-[12px]"
      />
      <FxBadge onClick={enterExpressionMode} disabled={disabled} />
    </div>
  )
}

interface FxBadgeProps {
  onClick: () => void
  disabled?: boolean
}

/**
 * Small monospace `fx` badge anchored at the top-right corner of the
 * input. Click switches to expression mode. Visually distinct from the
 * Sparkles "AI generate" pattern users associate that icon with.
 */
function FxBadge({ onClick, disabled }: FxBadgeProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title="Switch to expression (JSONata)"
      className={cn(
        'absolute -top-2 right-2 flex h-[16px] items-center rounded-[3px] px-1.5',
        'font-mono text-[9.5px] font-semibold uppercase tracking-wide',
        'bg-surface-2 text-text-faint',
        'transition-colors hover:bg-accent/15 hover:text-accent',
        disabled && 'pointer-events-none opacity-50',
      )}
    >
      fx
    </button>
  )
}
