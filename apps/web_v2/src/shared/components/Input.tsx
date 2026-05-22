import { forwardRef, type InputHTMLAttributes, type ReactNode, useId } from 'react'
import { cn } from '@/lib/cn'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  leftIcon?: ReactNode
  rightIcon?: ReactNode
  error?: boolean
  success?: boolean
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, leftIcon, rightIcon, error, success, id: idProp, ...props }, ref) => {
    const autoId = useId()
    const id = idProp ?? autoId

    return (
      <div
        className={cn(
          'flex items-center gap-2 px-3 h-9',
          'bg-bg border border-border-faint rounded-[8px]',
          'transition-[background-color,border-color] duration-[120ms]',
          error   ? 'border-err'
          : success ? 'border-ok'
          : 'hover:border-border-soft focus-within:border-border focus-within:bg-surface',
          className,
        )}
      >
        {leftIcon && (
          <span className={cn(
            'shrink-0 flex [&_svg]:w-3.5 [&_svg]:h-3.5 transition-colors',
            error ? 'text-err' : success ? 'text-ok' : 'text-text-faint',
          )}>
            {leftIcon}
          </span>
        )}
        <input
          ref={ref}
          id={id}
          className="flex-1 min-w-0 h-full bg-transparent border-none outline-none text-sm text-text placeholder:text-text-faint"
          aria-invalid={error ? 'true' : undefined}
          {...props}
        />
        {rightIcon && (
          <span className="text-text-faint shrink-0 flex [&_svg]:w-3.5 [&_svg]:h-3.5">{rightIcon}</span>
        )}
      </div>
    )
  },
)

Input.displayName = 'Input'
