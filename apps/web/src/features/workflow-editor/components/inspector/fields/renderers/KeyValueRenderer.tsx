import { Plus, X } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { RendererProps } from '../types'

type KVItem = { key: string; value: string }

function toKVArray(value: unknown): KVItem[] {
  if (Array.isArray(value)) return value.filter(v => typeof v === 'object' && v !== null) as KVItem[]
  if (typeof value === 'object' && value !== null) {
    return Object.entries(value as Record<string, unknown>).map(([k, v]) => ({ key: k, value: String(v ?? '') }))
  }
  return []
}

function fromKVArray(items: KVItem[]): Record<string, string> {
  return Object.fromEntries(items.map(i => [i.key, i.value]))
}

const CELL =
  'flex-1 min-w-0 flex items-center h-[32px] px-[10px] rounded-[6px] border border-[var(--border-soft)] bg-[rgba(255,255,255,0.025)] text-[12px] font-mono transition-colors hover:border-[var(--border)] focus-within:border-[var(--border)]'

export function KeyValueRenderer({ value, onChange, disabled }: RendererProps) {
  const items = toKVArray(value)

  const update = (index: number, field: 'key' | 'value', text: string) => {
    const next = items.map((item, i) => i === index ? { ...item, [field]: text } : item)
    onChange(fromKVArray(next))
  }

  const remove = (index: number) => {
    const next = items.filter((_, i) => i !== index)
    onChange(fromKVArray(next))
  }

  const add = () => onChange(fromKVArray([...items, { key: '', value: '' }]))

  return (
    <div className="flex flex-col gap-[6px]">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-[6px]">
          <label className={cn(CELL, 'text-[var(--text-mute)]')}>
            <input
              value={item.key}
              onChange={e => update(i, 'key', e.target.value)}
              placeholder="Key"
              disabled={disabled}
              className="w-full bg-transparent border-none outline-none text-[var(--text)] placeholder:text-[var(--text-faint)]"
            />
          </label>
          <label className={cn(CELL, 'text-[var(--text-mute)]')}>
            <input
              value={item.value}
              onChange={e => update(i, 'value', e.target.value)}
              placeholder="Value"
              disabled={disabled}
              className="w-full bg-transparent border-none outline-none text-[var(--text)] placeholder:text-[var(--text-faint)]"
            />
          </label>
          <button
            type="button"
            onClick={() => remove(i)}
            disabled={disabled}
            className="flex h-[28px] w-[28px] shrink-0 items-center justify-center rounded-[6px] text-[var(--text-faint)] transition-colors cursor-pointer hover:bg-[rgba(229,103,95,0.12)] hover:text-[var(--err)] disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Remove entry"
          >
            <X className="h-[13px] w-[13px]" strokeWidth={2} />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        disabled={disabled}
        className="inline-flex items-center gap-[6px] self-start py-[4px] px-0 text-[12px] font-medium text-[var(--accent)] bg-transparent border-none transition-opacity cursor-pointer hover:opacity-80 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <Plus className="w-[13px] h-[13px]" strokeWidth={2} />
        Add entry
      </button>
    </div>
  )
}
