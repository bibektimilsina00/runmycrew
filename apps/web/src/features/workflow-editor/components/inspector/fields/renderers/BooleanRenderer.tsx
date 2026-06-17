import { cn } from '@/lib/cn'
import type { RendererProps } from '../types'

/**
 * Linear-style flat toggle pill — track + sliding knob.
 * Sits inline at row height (19px) so it fits next to label/description
 * without inflating the row to a full 34px field shell.
 */
export function BooleanRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const checked = Boolean(value)
  return (
    <div className="flex items-center justify-between gap-[12px]">
      <span className="text-[12.5px] text-[var(--text-mute)]">
        {checked ? 'Enabled' : 'Disabled'}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={prop.label}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex w-[33px] h-[19px] rounded-[10px] p-0 transition-colors duration-150 cursor-pointer',
          checked ? 'bg-[var(--accent)]' : 'bg-[rgba(255,255,255,0.12)]',
          disabled && 'opacity-50 cursor-not-allowed',
        )}
      >
        <span
          className={cn(
            'absolute top-[2px] left-[2px] w-[15px] h-[15px] rounded-full bg-white transition-transform duration-150',
          )}
          style={{ transform: checked ? 'translateX(14px)' : 'translateX(0)' }}
        />
      </button>
    </div>
  )
}
