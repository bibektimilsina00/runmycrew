import { cn } from '@/lib/cn'
import type { RendererProps } from '../types'

export function NumberRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const opts = prop.typeOptions ?? {}
  const min = typeof opts.min === 'number' ? opts.min : undefined
  const max = typeof opts.max === 'number' ? opts.max : undefined
  const step = typeof opts.step === 'number' ? opts.step : 1

  const current = value === undefined || value === null || value === '' ? null : Number(value)
  const display = current === null ? '' : String(current)

  const clamp = (n: number) => {
    let next = n
    if (min !== undefined) next = Math.max(min, next)
    if (max !== undefined) next = Math.min(max, next)
    return next
  }

  const apply = (n: number | null) => onChange(n === null ? '' : n)
  const adjust = (delta: number) => {
    const base = current ?? min ?? 0
    apply(clamp(base + delta))
  }

  return (
    <div
      className={cn(
        'flex h-[34px] w-[128px] items-center rounded-[7px] border border-[var(--border-soft)] bg-[rgba(255,255,255,0.025)] overflow-hidden transition-colors',
        'hover:border-[var(--border)] focus-within:border-[var(--border)]',
        disabled && 'opacity-50 cursor-not-allowed',
      )}
    >
      <button
        type="button"
        onClick={() => adjust(-step)}
        disabled={disabled || (min !== undefined && current !== null && current <= min)}
        className="w-[36px] h-full text-[17px] leading-none text-[var(--text-mute)] transition-colors cursor-pointer hover:bg-[rgba(255,255,255,0.06)] hover:text-[var(--text)] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
        aria-label="Decrement"
      >
        −
      </button>
      <input
        type="number"
        value={display}
        onChange={e => apply(e.target.value === '' ? null : Number(e.target.value))}
        placeholder={prop.placeholder}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        className="flex-1 min-w-0 h-full bg-transparent text-center text-[13px] text-[var(--text)] font-mono outline-none border-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
      />
      <button
        type="button"
        onClick={() => adjust(step)}
        disabled={disabled || (max !== undefined && current !== null && current >= max)}
        className="w-[36px] h-full text-[17px] leading-none text-[var(--text-mute)] transition-colors cursor-pointer hover:bg-[rgba(255,255,255,0.06)] hover:text-[var(--text)] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
        aria-label="Increment"
      >
        +
      </button>
    </div>
  )
}
