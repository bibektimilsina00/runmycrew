import { useState, useRef, useEffect, useId, type ReactNode } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { cn } from '@/lib/cn'

export interface SelectOption {
  value: string
  label: string
  icon?: ReactNode
  description?: string
}

interface SelectProps {
  options: SelectOption[]
  value?: string
  onChange?: (value: string) => void
  placeholder?: string
  className?: string
  disabled?: boolean
  error?: boolean
  'aria-label'?: string
}

export function Select({ options, value, onChange, placeholder = 'Select…', className, disabled, error, 'aria-label': ariaLabel }: SelectProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const id = useId()
  const listId = `select-list-${id}`
  const selected = options.find(o => o.value === value)

  useEffect(() => {
    if (!open) return
    const onOutside = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { setOpen(false); return }
      if (e.key === 'ArrowDown') {
        const idx = options.findIndex(o => o.value === value)
        const next = options[Math.min(idx + 1, options.length - 1)]
        if (next) onChange?.(next.value)
      }
      if (e.key === 'ArrowUp') {
        const idx = options.findIndex(o => o.value === value)
        const prev = options[Math.max(idx - 1, 0)]
        if (prev) onChange?.(prev.value)
      }
    }
    document.addEventListener('mousedown', onOutside)
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('mousedown', onOutside); document.removeEventListener('keydown', onKey) }
  }, [open, options, value, onChange])

  return (
    <div ref={ref} className={cn('relative inline-block w-full', className)} data-state={open ? 'open' : 'closed'}>
      {/* Trigger — matches Input visual */}
      <button
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={ariaLabel}
        aria-invalid={error ? 'true' : undefined}
        disabled={disabled}
        onClick={() => !disabled && setOpen(o => !o)}
        className={cn(
          'flex items-center gap-2 w-full h-9 pl-3 pr-2.5 text-sm text-left',
          'bg-bg border border-border-faint rounded-[8px]',
          'transition-[background-color,border-color] duration-[120ms]',
          'disabled:opacity-40 disabled:cursor-not-allowed',
          error
            ? 'border-err'
            : open ? 'border-border bg-surface' : 'hover:border-border-soft',
        )}
      >
        <span className={cn('flex-1 min-w-0 truncate', !selected && 'text-text-faint')}>
          {selected ? (
            <span className="flex items-center gap-2">
              {selected.icon && <span className="shrink-0 flex text-text-faint [&_svg]:w-3.5 [&_svg]:h-3.5">{selected.icon}</span>}
              {selected.label}
            </span>
          ) : placeholder}
        </span>
        <ChevronDown size={13} className={cn('shrink-0 text-text-faint transition-transform duration-[150ms]', open && 'rotate-180')} />
      </button>

      {/* Dropdown */}
      <div
        id={listId}
        role="listbox"
        aria-label={ariaLabel}
        data-state={open ? 'open' : 'closed'}
        className={cn(
          'absolute top-[calc(100%+5px)] left-0 right-0 z-50',
          'bg-bg border border-border-faint rounded-[10px] p-1.5',
          'shadow-dropdown',
          'max-h-60 overflow-y-auto',
          'transition-[opacity,transform] duration-[150ms]',
          open ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 -translate-y-1 pointer-events-none',
        )}
      >
        {options.map(opt => (
          <button
            key={opt.value}
            type="button"
            role="option"
            aria-selected={opt.value === value}
            onClick={() => { onChange?.(opt.value); setOpen(false) }}
            className={cn(
              'flex items-center gap-2 w-full text-left px-2.5 py-1.5 rounded-[7px] text-sm',
              'transition-colors duration-[100ms]',
              opt.value === value
                ? 'bg-surface-2 text-text font-medium'
                : 'text-text-mute hover:bg-surface hover:text-text',
            )}
          >
            {opt.icon && <span className="shrink-0 flex text-text-faint [&_svg]:w-3.5 [&_svg]:h-3.5">{opt.icon}</span>}
            <span className="flex-1 min-w-0">
              <span className="block">{opt.label}</span>
              {opt.description && <span className="block text-xs text-text-faint mt-px">{opt.description}</span>}
            </span>
            {opt.value === value && <Check size={12} className="shrink-0 text-accent ml-auto" />}
          </button>
        ))}
      </div>
    </div>
  )
}
