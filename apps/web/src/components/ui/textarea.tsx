import { forwardRef, type TextareaHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>

/**
 * Fuse Textarea — styled to match Input.
 */
const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, ...props }, ref) => {
  return (
    <textarea
      ref={ref}
      className={cn(
        'flex min-h-[80px] w-full rounded-[8px] border border-border-faint bg-bg px-3 py-2 text-sm text-text',
        'placeholder:text-text-faint',
        'transition-[background-color,border-color] duration-[120ms]',
        'hover:border-border-soft',
        'focus-visible:outline-none focus-visible:border-border focus-visible:bg-surface',
        'disabled:cursor-not-allowed disabled:opacity-40',
        'resize-y',
        className,
      )}
      {...props}
    />
  )
})

Textarea.displayName = 'Textarea'

export { Textarea }
