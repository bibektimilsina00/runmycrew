import { forwardRef, type TextareaHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
  success?: boolean
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, success, ...props }, ref) => (
    <textarea
      ref={ref}
      aria-invalid={error ? 'true' : undefined}
      className={cn(
        'w-full resize-none outline-none',
        'bg-bg border border-border-faint rounded-[8px]',
        'px-3 py-2.5',
        'text-sm text-text placeholder:text-text-faint',
        'transition-[background-color,border-color] duration-[120ms]',
        error   ? 'border-err'
        : success ? 'border-ok'
        : 'hover:border-border-soft focus:border-border focus:bg-surface',
        className,
      )}
      {...props}
    />
  ),
)

Textarea.displayName = 'Textarea'
