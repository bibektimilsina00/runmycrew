import { useState } from 'react'
import { Sparkles } from 'lucide-react'
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
 * No separate UI flag — the rule "string starts with `=` → expression" lives
 * in one place and survives reload, copy-paste, and undo/redo without any
 * extra plumbing.
 */
export function StringRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const str = value === undefined || value === null ? '' : String(value)
  const opts = prop.typeOptions ?? {}
  const multiline = Boolean(opts.multiline)
  const rows = typeof opts.rows === 'number' ? opts.rows : 3
  const isExpression = str.startsWith('=')

  // Tracks whether the most recent mode change came from user action
  // (typing `$`, clicking the fx button) so the ExpressionEditor that
  // mounts next knows to grab focus + restore the caret. Without this the
  // renderer swap would unmount the user's focused input and they'd have
  // to click into the new editor to keep typing.
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
          className="pr-7 text-[12px] leading-relaxed"
        />
        <FxToggle onClick={enterExpressionMode} disabled={disabled} className="top-1.5 right-1.5" />
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
        className="h-8 pr-7 text-[12px]"
      />
      <FxToggle
        onClick={enterExpressionMode}
        disabled={disabled}
        className="top-1/2 right-1.5 -translate-y-1/2"
      />
    </div>
  )
}

interface FxToggleProps {
  onClick: () => void
  disabled?: boolean
  className?: string
}

function FxToggle({ onClick, disabled, className }: FxToggleProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title="Switch to expression (JSONata)"
      className={cn(
        'absolute flex h-5 w-5 items-center justify-center rounded-[4px] text-text-faint transition-colors hover:bg-accent/15 hover:text-accent',
        disabled && 'pointer-events-none opacity-50',
        className,
      )}
    >
      <Sparkles className="h-3 w-3" />
    </button>
  )
}
