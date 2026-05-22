import { cn } from '@/lib/cn'

type StatusDotStatus = 'ok' | 'warn' | 'err' | 'run' | 'draft'
type StatusDotSize = 'sm' | 'md'

interface StatusDotProps {
  status: StatusDotStatus
  size?: StatusDotSize
  className?: string
}

const sizeMap: Record<StatusDotSize, string> = {
  sm: 'w-[6px] h-[6px]',
  md: 'w-[8px] h-[8px]',
}

const statusMap: Record<StatusDotStatus, string> = {
  ok:    'bg-ok shadow-[0_0_6px_oklch(0.78_0.14_145_/_0.5)]',
  warn:  'bg-warn',
  err:   'bg-err shadow-[0_0_6px_oklch(0.70_0.18_22_/_0.5)]',
  run:   'bg-accent animate-status-pulse',
  draft: 'bg-text-dim',
}

export function StatusDot({ status, size = 'md', className }: StatusDotProps) {
  return (
    <span
      className={cn(
        'inline-block shrink-0 rounded-full',
        sizeMap[size],
        statusMap[status],
        className,
      )}
    />
  )
}
