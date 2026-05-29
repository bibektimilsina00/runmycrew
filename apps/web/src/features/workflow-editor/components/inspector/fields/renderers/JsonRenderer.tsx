import { useState } from 'react'
import { Textarea } from '@/shared/components'
import { cn } from '@/lib/cn'
import type { NodeProperty } from '../../../../types/editorTypes'

interface Props {
  prop: NodeProperty
  value: unknown
  onChange: (value: unknown) => void
}

function toJsonString(value: unknown): string {
  if (value === undefined || value === null || value === '') return ''
  if (typeof value === 'string') return value
  return JSON.stringify(value, null, 2)
}

export function JsonRenderer({ prop, value, onChange }: Props) {
  const [raw, setRaw] = useState(() => toJsonString(value))
  const [invalid, setInvalid] = useState(false)
  const opts = prop.typeOptions ?? {}
  const rows = typeof opts.rows === 'number' ? opts.rows : 6

  const handleChange = (text: string) => {
    setRaw(text)
    if (!text.trim()) { setInvalid(false); onChange(''); return }
    try {
      onChange(JSON.parse(text))
      setInvalid(false)
    } catch {
      setInvalid(true)
      onChange(text)
    }
  }

  return (
    <div className="flex flex-col gap-1">
      <Textarea
        value={raw}
        onChange={e => handleChange(e.target.value)}
        rows={rows}
        spellCheck={false}
        placeholder={prop.placeholder ?? '{}'}
        className={cn(
          'font-mono text-[11px] leading-relaxed',
          invalid && 'border-err focus-visible:ring-err/30',
        )}
      />
      {invalid && <p className="text-[10px] text-err">Invalid JSON</p>}
    </div>
  )
}
