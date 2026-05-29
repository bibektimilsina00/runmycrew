import { Plus, X } from 'lucide-react'
import { Input } from '@/shared/components'
import type { NodeProperty } from '../../../../types/editorTypes'

interface Props {
  prop: NodeProperty
  value: unknown
  onChange: (value: unknown) => void
}

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

export function KeyValueRenderer({ value, onChange }: Props) {
  const items = toKVArray(value)

  const update = (index: number, field: 'key' | 'value', text: string) => {
    const next = items.map((item, i) => i === index ? { ...item, [field]: text } : item)
    onChange(fromKVArray(next))
  }

  const remove = (index: number) => {
    const next = items.filter((_, i) => i !== index)
    onChange(fromKVArray(next))
  }

  const add = () => {
    onChange(fromKVArray([...items, { key: '', value: '' }]))
  }

  return (
    <div className="flex flex-col gap-1.5">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <Input
            value={item.key}
            onChange={e => update(i, 'key', e.target.value)}
            placeholder="Key"
            className="h-7 flex-1 text-[11px]"
          />
          <Input
            value={item.value}
            onChange={e => update(i, 'value', e.target.value)}
            placeholder="Value"
            className="h-7 flex-1 text-[11px]"
          />
          <button
            type="button"
            onClick={() => remove(i)}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[6px] text-text-faint hover:bg-surface hover:text-err transition-colors"
          >
            <X size={12} />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        className="flex h-7 w-full items-center justify-center gap-1.5 rounded-[7px] border border-dashed border-border-faint text-[11px] text-text-faint hover:border-border-soft hover:text-text-mute transition-colors"
      >
        <Plus size={11} />
        Add entry
      </button>
    </div>
  )
}
