import { Input, Textarea } from '@/shared/components'
import type { RendererProps } from '../types'

export function StringRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const str = value === undefined || value === null ? '' : String(value)
  const opts = prop.typeOptions ?? {}

  if (opts.multiline) {
    return (
      <Textarea
        value={str}
        onChange={e => onChange(e.target.value)}
        rows={typeof opts.rows === 'number' ? opts.rows : 3}
        placeholder={prop.placeholder}
        disabled={disabled}
        className="text-[12px] leading-relaxed"
      />
    )
  }

  return (
    <Input
      type={opts.password ? 'password' : 'text'}
      value={str}
      onChange={e => onChange(e.target.value)}
      placeholder={prop.placeholder}
      disabled={disabled}
      className="h-8 text-[12px]"
    />
  )
}
