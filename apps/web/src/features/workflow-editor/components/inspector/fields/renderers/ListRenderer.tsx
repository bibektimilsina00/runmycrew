import { Plus, X } from 'lucide-react'
import { Input } from '@/shared/components'
import type { NodeProperty } from '../../../../types/editorTypes'

interface Props {
  prop: NodeProperty
  value: unknown
  onChange: (value: unknown) => void
}

function toStringArray(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String)
  if (typeof value === 'string' && value.trim()) {
    try { const p = JSON.parse(value); return Array.isArray(p) ? p.map(String) : [value] } catch { return [value] }
  }
  return []
}

export function ListRenderer({ prop, value, onChange }: Props) {
  const items = toStringArray(value)
  const opts = prop.typeOptions ?? {}
  const addLabel = typeof opts.addButtonText === 'string' ? opts.addButtonText : 'Add item'

  const update = (i: number, text: string) => {
    onChange(items.map((v, j) => j === i ? text : v))
  }

  const remove = (i: number) => {
    onChange(items.filter((_, j) => j !== i))
  }

  const add = () => {
    onChange([...items, ''])
  }

  return (
    <div className="flex flex-col gap-1.5">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <Input
            value={item}
            onChange={e => update(i, e.target.value)}
            placeholder={`Item ${i + 1}`}
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
        {addLabel}
      </button>
    </div>
  )
}
