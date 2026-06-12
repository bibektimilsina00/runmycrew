import { Input } from '@/shared/components'
import type { RendererProps } from '../types'

export function NumberRenderer({ prop, value, onChange, disabled }: RendererProps) {
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
      disabled={disabled}
      className="h-8 rounded-[5px] text-[12px]"
    />
  )
}
