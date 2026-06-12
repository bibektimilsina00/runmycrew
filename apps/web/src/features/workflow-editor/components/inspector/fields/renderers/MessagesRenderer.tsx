import { useEffect, useRef, useState } from 'react'
import { Plus, X } from 'lucide-react'
import { Textarea } from '@/shared/components'
import { cn } from '@/lib/cn'
import type { RendererProps } from '../types'
import { ExpressionEditor } from '../expression/ExpressionEditor'

interface Message {
  role: 'system' | 'user' | 'assistant'
  content: string
}

const ROLES: Message['role'][] = ['system', 'user', 'assistant']

const ROLE_STYLES: Record<Message['role'], string> = {
  system: 'bg-[var(--accent-line)]/10 text-[var(--accent)] border-[var(--accent-line)]/30',
  user: 'bg-surface text-text-mute border-border-faint',
  assistant: 'bg-ok/10 text-ok border-ok/30',
}

function toMessages(value: unknown): Message[] {
  if (Array.isArray(value)) {
    return value
      .filter(v => typeof v === 'object' && v !== null)
      .map(v => {
        const obj = v as Record<string, unknown>
        return { role: (ROLES.includes(obj.role as Message['role']) ? obj.role : 'user') as Message['role'], content: String(obj.content ?? '') }
      })
  }
  if (typeof value === 'string' && value.trim()) {
    try { const p = JSON.parse(value); return Array.isArray(p) ? toMessages(p) : [] } catch { return [] }
  }
  return []
}

export function MessagesRenderer({ value, onChange, disabled }: RendererProps) {
  const messages = toMessages(value)

  const updateRole = (i: number, role: Message['role']) => {
    onChange(messages.map((m, j) => j === i ? { ...m, role } : m))
  }

  const updateContent = (i: number, content: string) => {
    onChange(messages.map((m, j) => j === i ? { ...m, content } : m))
  }

  const remove = (i: number) => {
    onChange(messages.filter((_, j) => j !== i))
  }

  const add = () => {
    onChange([...messages, { role: 'user', content: '' }])
  }

  return (
    <div className="flex flex-col gap-2">
      {messages.map((msg, i) => (
        <MessageRow
          // Key by index — messages reorder rarely; if they ever did, callers
          // would need a stable id. Today the array is append-only / removed
          // from the tail in practice.
          key={i}
          message={msg}
          onChangeRole={role => updateRole(i, role)}
          onChangeContent={content => updateContent(i, content)}
          onRemove={() => remove(i)}
          disabled={disabled}
        />
      ))}
      <button
        type="button"
        onClick={add}
        disabled={disabled}
        className="flex h-7 w-full items-center justify-center gap-1.5 rounded-[7px] border border-dashed border-border-faint text-[11px] text-text-faint hover:border-border-soft hover:text-text-mute transition-colors disabled:opacity-40"
      >
        <Plus size={11} />
        Add message
      </button>
    </div>
  )
}

interface MessageRowProps {
  message: Message
  onChangeRole: (role: Message['role']) => void
  onChangeContent: (content: string) => void
  onRemove: () => void
  disabled?: boolean
}

/**
 * One message in the agent / LLM messages list. Owns its dual-mode state
 * (plain textarea vs JSONata expression editor) the same way `StringRenderer`
 * does for top-level string fields. Lives in its own component so the
 * autoFocus flags don't leak across messages.
 */
function MessageRow({
  message,
  onChangeRole,
  onChangeContent,
  onRemove,
  disabled,
}: MessageRowProps) {
  const isExpression = message.content.startsWith('=')

  const [autoFocusOnEnter, setAutoFocusOnEnter] = useState(false)
  const [autoFocusOnExit, setAutoFocusOnExit] = useState(false)
  const plainFieldRef = useFocusOnExit<HTMLTextAreaElement>(autoFocusOnExit, () =>
    setAutoFocusOnExit(false),
  )

  const toggleExpressionMode = () => {
    if (isExpression) {
      setAutoFocusOnExit(true)
      onChangeContent(message.content.slice(1))
    } else {
      setAutoFocusOnEnter(true)
      onChangeContent(`=${message.content}`)
    }
  }

  // Type `=` or `$` as the first character to promote to expression mode
  // (same shortcut as StringRenderer).
  const handlePlainTyped = (next: string) => {
    const enteringExpression =
      !message.content.startsWith('=') && (next.startsWith('=') || next.startsWith('$'))
    if (enteringExpression) setAutoFocusOnEnter(true)
    if (next.startsWith('$') && !message.content.startsWith('=')) {
      onChangeContent(`=${next}`)
      return
    }
    onChangeContent(next)
  }

  // Deleting back past the `=` exits expression mode. Re-arm focus so the
  // plain textarea takes the next keystroke (otherwise focus drops to
  // <body> and a held backspace deletes the selected workflow node).
  const handleExpressionTyped = (next: string) => {
    if (!next.startsWith('=') && message.content.startsWith('=')) {
      setAutoFocusOnExit(true)
    }
    onChangeContent(next)
  }

  const placeholder =
    message.role === 'system'
      ? 'System instructions…'
      : message.role === 'user'
        ? 'Hello {{trigger.output}} or =$trigger.message'
        : 'Assistant response…'

  return (
    <div className="flex flex-col gap-1 rounded-[5px] border border-border-faint bg-bg p-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex gap-1">
          {ROLES.map(role => (
            <button
              key={role}
              type="button"
              onClick={() => onChangeRole(role)}
              className={cn(
                'rounded-[5px] border px-2 py-0.5 text-[10px] font-medium transition-colors',
                message.role === role ? ROLE_STYLES[role] : 'border-transparent text-text-faint hover:text-text-mute',
              )}
            >
              {role}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={toggleExpressionMode}
            disabled={disabled}
            title={isExpression ? 'Switch to plain text' : 'Switch to expression (JSONata)'}
            aria-pressed={isExpression}
            className={cn(
              'flex h-5 items-center rounded-[3px] px-1.5',
              'font-mono text-[10px] font-semibold uppercase tracking-wide leading-none',
              'transition-colors',
              isExpression
                ? 'bg-accent/15 text-accent hover:bg-accent/25'
                : 'text-text-faint hover:bg-accent/15 hover:text-accent',
              disabled && 'pointer-events-none opacity-50',
            )}
          >
            fx
          </button>
          <button
            type="button"
            onClick={onRemove}
            className="flex h-5 w-5 items-center justify-center rounded text-text-faint hover:text-err transition-colors"
          >
            <X size={11} />
          </button>
        </div>
      </div>
      {isExpression ? (
        <ExpressionEditor
          value={message.content}
          onChange={handleExpressionTyped}
          placeholder={placeholder}
          multiline
          rows={2}
          disabled={disabled}
          autoFocus={autoFocusOnEnter}
          onAutoFocusDone={() => setAutoFocusOnEnter(false)}
        />
      ) : (
        <Textarea
          ref={plainFieldRef}
          value={message.content}
          onChange={e => handlePlainTyped(e.target.value)}
          rows={2}
          placeholder={placeholder}
          className="min-h-[52px] rounded-[5px] text-[11px] leading-relaxed"
          disabled={disabled}
        />
      )}
    </div>
  )
}

/**
 * Callback ref that focuses the plain textarea once when the parent flag
 * flips true (i.e. the renderer just swapped back from expression mode).
 * Mirror of the helper in `StringRenderer` — kept here rather than
 * extracted because the message-row variant only ever wraps a textarea,
 * which lets the generic eliminate the input/textarea union.
 */
function useFocusOnExit<T extends HTMLTextAreaElement>(
  shouldFocus: boolean,
  onDone: () => void,
) {
  const ref = useRef<T | null>(null)
  useEffect(() => {
    if (!shouldFocus) return
    const el = ref.current
    if (!el) return
    el.focus()
    const pos = el.value.length
    el.setSelectionRange(pos, pos)
    onDone()
  }, [shouldFocus, onDone])
  return (node: T | null) => {
    ref.current = node
  }
}
