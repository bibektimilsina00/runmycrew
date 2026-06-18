import { forwardRef, type InputHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

export type InputProps = InputHTMLAttributes<HTMLInputElement>

/**
 * Fuse Input — styled to match the design system.
 * Uses Radix-compatible patterns; wrap with FormField for label + error.
 */
const Input = forwardRef<HTMLInputElement, InputProps>(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      ref={ref}
      className={cn(
        'flex h-9 w-full rounded-[8px] border border-border-faint bg-bg px-3 text-sm text-text',
        'placeholder:text-text-faint',
        'transition-[background-color,border-color] duration-[120ms]',
        'hover:border-border-soft',
        'focus-visible:outline-none focus-visible:border-border focus-visible:bg-surface',
        'disabled:cursor-not-allowed disabled:opacity-40',
        'aria-[invalid=true]:border-err',
        className,
      )}
      {...props}
    />
  )
})

Input.displayName = 'Input'

export { Input }
