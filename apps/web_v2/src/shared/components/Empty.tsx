import { type ReactNode } from 'react'
import { cn } from '@/lib/cn'

interface EmptyProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function Empty({ icon, title, description, action, className }: EmptyProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-2 py-12 px-6 text-center', className)}>
      {icon && (
        <div className="w-11 h-11 rounded-md bg-surface-2 border border-border-faint flex items-center justify-center text-text-faint mb-1 shrink-0 [&_svg]:w-5 [&_svg]:h-5">
          {icon}
        </div>
      )}
      <span className="text-sm font-medium text-text">{title}</span>
      {description && (
        <span className="text-xs text-text-faint max-w-[200px] leading-relaxed">{description}</span>
      )}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}
