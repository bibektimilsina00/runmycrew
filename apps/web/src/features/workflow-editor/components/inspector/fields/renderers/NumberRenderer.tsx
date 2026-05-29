import { Input } from '@/shared/components'
import type { NodeProperty } from '../../../../types/editorTypes'

interface Props {
  prop: NodeProperty
  value: unknown
  onChange: (value: unknown) => void
}

export function NumberRenderer({ prop, value, onChange }: Props) {
  const opts = prop.typeOptions ?? {}
  const str = value === undefined || value === null ? '' : String(value)

  return (
    <Input
      type="number"
      value={str}
      onChange={e => onChange(e.target.value === '' ? '' : Number(e.target.value))}
      placeholder={prop.placeholder}
      min={opts.min !== undefined ? String(opts.min) : undefined}
      max={opts.max !== undefined ? String(opts.max) : undefined}
      step={opts.step !== undefined ? String(opts.step) : undefined}
      className="h-8 text-[12px]"
    />
  )
}
