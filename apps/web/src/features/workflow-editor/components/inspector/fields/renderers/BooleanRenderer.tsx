import { Toggle } from '@/shared/components'
import { cn } from '@/lib/cn'
import type { NodeProperty } from '../../../../types/editorTypes'

interface Props {
  prop: NodeProperty
  value: unknown
  onChange: (value: unknown) => void
}

export function BooleanRenderer({ prop, value, onChange }: Props) {
  const checked = Boolean(value)
  return (
    <div className="flex h-8 items-center justify-between rounded-[8px] border border-border-faint bg-bg px-3">
      <span className={cn('text-[12px]', checked ? 'text-text-mute' : 'text-text-faint')}>
        {checked ? 'Enabled' : 'Disabled'}
      </span>
      <Toggle
        checked={checked}
        onChange={e => onChange(e.target.checked)}
        aria-label={prop.label}
      />
    </div>
  )
}
