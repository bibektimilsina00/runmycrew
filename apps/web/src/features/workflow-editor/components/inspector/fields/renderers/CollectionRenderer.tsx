import { Plus, X, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/cn'
import type { NodeDefinition, NodeProperty } from '../../../../types/editorTypes'
import { shouldShowProperty } from '../../../../utils/nodeUtils'
// Lazy import to avoid circular dep — PropertyField imports from this registry
import { PropertyField } from '../PropertyField'
import type { RendererProps } from '../types'

type CollectionItem = Record<string, unknown>

function toItemArray(value: unknown): CollectionItem[] {
  if (Array.isArray(value)) return value.filter(v => typeof v === 'object' && v !== null) as CollectionItem[]
  if (typeof value === 'object' && value !== null) return [value as CollectionItem]
  return []
}

export function CollectionRenderer({ prop, definition, value, onChange, properties }: RendererProps) {
  const opts = prop.typeOptions ?? {}
  const multipleValues = opts.multipleValues ?? false
  const addLabel = typeof opts.addButtonText === 'string' ? opts.addButtonText : 'Add item'
  const subProps = prop.properties ?? []

  if (!multipleValues) {
    const item = (typeof value === 'object' && value !== null && !Array.isArray(value) ? value : {}) as CollectionItem
    return (
      <SingleItem
        subProps={subProps}
        definition={definition}
        item={item}
        onChange={onChange}
        allValues={properties}
      />
    )
  }

  const items = toItemArray(value)

  const updateItem = (i: number, key: string, val: unknown) => {
    onChange(items.map((item, j) => j === i ? { ...item, [key]: val } : item))
  }

  const removeItem = (i: number) => {
    onChange(items.filter((_, j) => j !== i))
  }

  const addItem = () => {
    const defaults: CollectionItem = {}
    for (const p of subProps) {
      if (p.default !== undefined) defaults[p.name] = p.default
    }
    onChange([...items, defaults])
  }

  return (
    <div className="flex flex-col gap-2">
      {items.map((item, i) => (
        <CollapsibleItem
          key={i}
          index={i}
          subProps={subProps}
          definition={definition}
          item={item}
          onUpdate={(key, val) => updateItem(i, key, val)}
          onRemove={() => removeItem(i)}
          allValues={properties}
        />
      ))}
      <button
        type="button"
        onClick={addItem}
        className="flex h-7 w-full items-center justify-center gap-1.5 rounded-[7px] border border-dashed border-border-faint text-[11px] text-text-faint hover:border-border-soft hover:text-text-mute transition-colors"
      >
        <Plus size={11} />
        {addLabel}
      </button>
    </div>
  )
}

// ── Single item (no multiple values) ─────────────────────────────────────────

interface SingleItemProps {
  subProps: NodeProperty[]
  definition: NodeDefinition
  item: CollectionItem
  onChange: (value: unknown) => void
  allValues: Record<string, unknown>
}

function SingleItem({ subProps, definition, item, onChange, allValues }: SingleItemProps) {
  const visible = subProps.filter(p => p.visibility !== 'hidden' && shouldShowProperty(p, { ...allValues, ...item }))
  return (
    <div className="flex flex-col gap-3 rounded-[8px] border border-border-faint bg-bg p-3">
      {visible.map(p => (
        <PropertyField
          key={p.name}
          prop={p}
          definition={definition}
          properties={{ ...allValues, ...item }}
          value={item[p.name]}
          onChange={(val) => onChange({ ...item, [p.name]: val })}
        />
      ))}
    </div>
  )
}

// ── Collapsible item (multiple values) ───────────────────────────────────────

interface CollapsibleItemProps {
  index: number
  subProps: NodeProperty[]
  definition: NodeDefinition
  item: CollectionItem
  onUpdate: (key: string, val: unknown) => void
  onRemove: () => void
  allValues: Record<string, unknown>
}

function CollapsibleItem({ index, subProps, definition, item, onUpdate, onRemove, allValues }: CollapsibleItemProps) {
  const [open, setOpen] = useState(true)
  const visible = subProps.filter(p => p.visibility !== 'hidden' && shouldShowProperty(p, { ...allValues, ...item }))

  return (
    <div className="rounded-[8px] border border-border-faint bg-bg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2">
        <button
          type="button"
          onClick={() => setOpen(v => !v)}
          className="flex flex-1 items-center gap-1.5 text-left text-[11px] font-medium text-text-mute"
        >
          <ChevronDown size={12} className={cn('shrink-0 transition-transform', !open && '-rotate-90')} />
          Item {index + 1}
        </button>
        <button
          type="button"
          onClick={onRemove}
          className="flex h-5 w-5 items-center justify-center rounded text-text-faint hover:text-err transition-colors"
        >
          <X size={11} />
        </button>
      </div>
      {open && (
        <div className="flex flex-col gap-3 border-t border-border-faint p-3">
          {visible.map(p => (
            <PropertyField
              key={p.name}
              prop={p}
              definition={definition}
              properties={{ ...allValues, ...item }}
              value={item[p.name]}
              onChange={(val) => onUpdate(p.name, val)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
