import { Plus, X } from 'lucide-react'
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
        return {
          role: (ROLES.includes(obj.role as Message['role']) ? obj.role : 'user') as Message['role'],
          content: String(obj.content ?? ''),
        }
      })
  }
  if (typeof value === 'string' && value.trim()) {
    try {
      const p = JSON.parse(value)
      return Array.isArray(p) ? toMessages(p) : []
    } catch {
      return []
    }
  }
  return []
}

export function MessagesRenderer({ value, onChange, disabled }: RendererProps) {
  const messages = toMessages(value)

  const updateRole = (i: number, role: Message['role']) => {
    onChange(messages.map((m, j) => (j === i ? { ...m, role } : m)))
  }

  const updateContent = (i: number, content: string) => {
    onChange(messages.map((m, j) => (j === i ? { ...m, content } : m)))
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
 * One message in the agent / LLM messages list. Content edits go
 * through `ExpressionEditor` — same component every other string
 * field uses, so inline `{{ $step.x }}` autocompletion + JSONata
 * syntax highlighting + the upstream-tree drag-drop all work the
 * same way they do on a regular text field. The legacy dual-mode
 * `=expression` toggle was dropped: ExpressionEditor already
 * migrates `=expr` → `{{ expr }}` on first edit, so the new mixed-
 * mode editor handles every case without a manual switch.
 */
function MessageRow({
  message,
  onChangeRole,
  onChangeContent,
  onRemove,
  disabled,
}: MessageRowProps) {
  const placeholder =
    message.role === 'system'
      ? 'System instructions — e.g. "You are a helpful assistant."'
      : message.role === 'user'
        ? 'User message — supports {{ $step.field }} expressions'
        : 'Assistant response — supports {{ $step.field }} expressions'

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
                message.role === role
                  ? ROLE_STYLES[role]
                  : 'border-transparent text-text-faint hover:text-text-mute',
              )}
            >
              {role}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={onRemove}
          className="flex h-5 w-5 items-center justify-center rounded text-text-faint hover:text-err transition-colors"
          title="Remove message"
        >
          <X size={11} />
        </button>
      </div>
      <ExpressionEditor
        value={message.content}
        onChange={onChangeContent}
        placeholder={placeholder}
        multiline
        rows={2}
        disabled={disabled}
      />
    </div>
  )
}
