import { type ReactNode } from 'react'
import { cn } from '@/lib/cn'

type BadgeVariant = 'default' | 'ok' | 'warn' | 'err' | 'accent' | 'draft'

interface BadgeProps {
  variant?: BadgeVariant
  children: ReactNode
  className?: string
  dot?: boolean
}

// All backgrounds are solid opaque CSS variables — no transparency
const variants: Record<BadgeVariant, string> = {
  default: 'bg-surface-2 text-text-mute border border-border-faint',
  ok:      'bg-[var(--badge-ok-bg)] text-ok',
  warn:    'bg-[var(--badge-warn-bg)] text-warn',
  err:     'bg-[var(--badge-err-bg)] text-err',
  accent:  'bg-[var(--badge-acc-bg)] text-accent',
  draft:   'bg-surface text-text-mute border border-border-faint',
}

const dotColors: Record<BadgeVariant, string> = {
  default: 'bg-text-dim',
  ok:      'bg-ok shadow-[0_0_5px_var(--ok)]',
  warn:    'bg-warn',
  err:     'bg-err shadow-[0_0_5px_var(--err)]',
  accent:  'bg-accent',
  draft:   'bg-text-dim',
}

export function Badge({ variant = 'default', children, className, dot }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1',
        'font-mono text-[10px] font-medium uppercase tracking-[0.08em]',
        'px-2 py-[3px] rounded-[4px] leading-none',
        variants[variant],
        className,
      )}
    >
      {dot && <span className={cn('w-1 h-1 rounded-full shrink-0', dotColors[variant])} />}
      {children}
    </span>
  )
}
