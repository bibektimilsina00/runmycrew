import { type ChangeEvent } from 'react'
import { Check } from 'lucide-react'
import { cn } from '@/lib/cn'

interface CheckboxProps {
  checked?: boolean
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void
  label?: string
  className?: string
  id?: string
}

export function Checkbox({ checked = false, onChange, label, className, id }: CheckboxProps) {
  const inputId = id ?? (label ? `cb-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined)

  return (
    <label
      htmlFor={inputId}
      className={cn('group inline-flex items-center gap-[7px] cursor-pointer select-none', className)}
    >
      <div
        className={cn(
          'relative w-[14px] h-[14px] shrink-0 rounded-[4px] border',
          'transition-[background,border-color] duration-[120ms]',
          checked
            ? 'bg-text border-text'
            : 'bg-bg border-border-faint group-hover:border-border-soft',
        )}
      >
        <input
          id={inputId}
          type="checkbox"
          checked={checked}
          onChange={onChange}
          className="sr-only"
        />
        {checked && (
          <Check
            size={10}
            strokeWidth={3}
            className="absolute inset-0 m-auto text-bg"
          />
        )}
      </div>
      {label && (
        <span className="text-[13px] text-text-mute group-hover:text-text transition-colors duration-[120ms] leading-none">{label}</span>
      )}
    </label>
  )
}
