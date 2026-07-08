import { forwardRef, type TextareaHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>

/**
 * RunMyCrew Textarea — styled to match Input.
 */
const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, ...props }, ref) => {
  return (
    <textarea
      ref={ref}
      className={cn(
        'flex min-h-[80px] w-full rounded-[8px] border border-border-soft bg-bg2 px-3 py-2 text-sm text-text',
        'placeholder:text-text-faint',
        'transition-[background-color,border-color] [transition-duration:120ms]',
        'hover:border-border hover:bg-surface',
        'focus-visible:outline-none focus-visible:border-accent focus-visible:bg-surface-2',
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
