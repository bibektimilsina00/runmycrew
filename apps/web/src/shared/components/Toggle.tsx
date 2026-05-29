import { type ChangeEvent } from 'react'
import { cn } from '@/lib/cn'

interface ToggleProps {
  checked?: boolean
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void
  className?: string
  'aria-label'?: string
}

export function Toggle({ checked = false, onChange, className, 'aria-label': ariaLabel }: ToggleProps) {
  return (
    <label
      className={cn('relative inline-flex items-center cursor-pointer shrink-0 select-none', className)}
      aria-label={ariaLabel}
    >
      <input
        type="checkbox"
        role="switch"
        aria-checked={checked}
        checked={checked}
        onChange={onChange}
        className="sr-only"
      />
      {/* Track 34×20 */}
      <div
        className={cn(
          'w-[34px] h-[20px] rounded-full border',
          'transition-[background,border-color] duration-[160ms]',
          checked
            ? 'bg-text border-text'
            : 'bg-surface border-border-faint hover:border-border-soft',
        )}
      />
      {/* Thumb 14×14 */}
      <div
        className={cn(
          'absolute top-[2px] left-[2px] w-[14px] h-[14px] rounded-full',
          'transition-[transform,background-color] duration-[200ms] ease-spring',
          checked
            ? 'bg-bg translate-x-[14px]'
            : 'bg-text-mute',
        )}
      />
    </label>
  )
}
