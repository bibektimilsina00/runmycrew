import { Plus, X } from 'lucide-react'
import { Textarea } from '@/shared/components'
import { cn } from '@/lib/cn'
import type { RendererProps } from '../types'

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
        <div key={i} className="flex flex-col gap-1 rounded-[5px] border border-border-faint bg-bg p-2">
          <div className="flex items-center justify-between gap-2">
            <div className="flex gap-1">
              {ROLES.map(role => (
                <button
                  key={role}
                  type="button"
                  onClick={() => updateRole(i, role)}
                  className={cn(
                    'rounded-[5px] border px-2 py-0.5 text-[10px] font-medium transition-colors',
                    msg.role === role ? ROLE_STYLES[role] : 'border-transparent text-text-faint hover:text-text-mute',
                  )}
                >
                  {role}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={() => remove(i)}
              className="flex h-5 w-5 items-center justify-center rounded text-text-faint hover:text-err transition-colors"
            >
              <X size={11} />
            </button>
          </div>
          <Textarea
            value={msg.content}
            onChange={e => updateContent(i, e.target.value)}
            rows={2}
            placeholder={msg.role === 'system' ? 'System instructions…' : msg.role === 'user' ? '{{trigger.output}}' : 'Assistant response…'}
            className="min-h-[52px] rounded-[5px] text-[11px] leading-relaxed"
          />
        </div>
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
