import { Toggle } from '@/shared/components'
import { cn } from '@/lib/cn'
import type { RendererProps } from '../types'

export function BooleanRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const checked = Boolean(value)
  return (
    <div className="flex h-8 items-center justify-between rounded-[8px] border border-border-faint bg-bg px-3">
      <span className={cn('text-[12px]', checked ? 'text-text-mute' : 'text-text-faint')}>
        {checked ? 'Enabled' : 'Disabled'}
      </span>
      <Toggle
        checked={checked}
        onChange={e => onChange(e.target.checked)}
        disabled={disabled}
        aria-label={prop.label}
      />
    </div>
  )
}
