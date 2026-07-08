import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react'
import { cn } from '@/lib/cn'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  leftIcon?: ReactNode
  rightIcon?: ReactNode
  error?: boolean
  success?: boolean
}

/**
 * RunMyCrew Input — styled to match the design system.
 * Wraps or outputs native input and supports legacy leftIcon/rightIcon and validation states.
 */
const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, leftIcon, rightIcon, error, success, ...props }, ref) => {
    const hasAddon = Boolean(leftIcon || rightIcon)

    if (!hasAddon && !error && !success) {
      return (
        <input
          type={type}
          ref={ref}
          className={cn(
            'flex h-9 w-full rounded-[8px] border border-border-soft bg-surface px-3 text-sm text-text',
            'placeholder:text-text-faint',
            'transition-[background-color,border-color] [transition-duration:120ms]',
            'hover:border-border hover:bg-surface-2',
            'focus-visible:outline-none focus-visible:border-accent focus-visible:bg-surface-2',
            'disabled:cursor-not-allowed disabled:opacity-40',
            'aria-[invalid=true]:border-err',
            className,
          )}
          {...props}
        />
      )
    }

    return (
      <div
        className={cn(
          'flex items-center gap-2 px-3 h-9 w-full rounded-[8px] border bg-surface',
          'transition-[background-color,border-color] [transition-duration:120ms]',
          error
            ? 'border-err'
            : success
            ? 'border-ok'
            : 'border-border-soft hover:border-border hover:bg-surface-2 focus-within:border-accent focus-within:bg-surface-2',
          className,
        )}
      >
        {leftIcon && (
          <span
            className={cn(
              'shrink-0 flex [&_svg]:w-3.5 [&_svg]:h-3.5 transition-colors [transition-duration:120ms]',
              error ? 'text-err' : success ? 'text-ok' : 'text-text-faint',
            )}
          >
            {leftIcon}
          </span>
        )}
        <input
          type={type}
          ref={ref}
          className="flex-1 min-w-0 h-full bg-transparent border-none outline-none text-sm text-text placeholder:text-text-faint"
          aria-invalid={error ? 'true' : undefined}
          {...props}
        />
        {rightIcon && (
          <span className="text-text-faint shrink-0 flex [&_svg]:w-3.5 [&_svg]:h-3.5">
            {rightIcon}
          </span>
        )}
      </div>
    )
  },
)

Input.displayName = 'Input'

export { Input }
