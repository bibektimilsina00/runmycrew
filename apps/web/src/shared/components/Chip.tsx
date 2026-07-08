import { type ReactNode } from 'react'
import { cn } from '@/lib/cn'

interface ChipProps {
  active?: boolean
  onClick?: () => void
  children: ReactNode
  leftIcon?: ReactNode
  className?: string
}

export function Chip({ active, onClick, children, leftIcon, className }: ChipProps) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={active}
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5',
        'px-3 py-1.5 rounded-full border',
        'text-xs font-medium',
        'transition-[background,color,border-color] [transition-duration:120ms]',
        'cursor-pointer select-none',
        active
          ? 'bg-surface-2 border-border text-text'
          : 'bg-transparent border-border text-text-faint hover:bg-surface hover:text-text',
        className,
      )}
    >
      {active && (
        <span className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
      )}
      {leftIcon && !active && (
        <span className="shrink-0 flex [&_svg]:w-2.5 [&_svg]:h-2.5">{leftIcon}</span>
      )}
      {children}
    </button>
  )
}
