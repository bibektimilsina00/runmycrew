import { type ReactNode } from 'react'
import { cn } from '@/lib/cn'

type CardPadding = 'sm' | 'md' | 'lg' | 'none'

interface CardProps {
  children: ReactNode
  className?: string
  padding?: CardPadding
  elevated?: boolean
}

const paddingMap: Record<CardPadding, string> = {
  none: '',
  sm:   'p-3',
  md:   'p-4',
  lg:   'p-5',
}

export function Card({ children, className, padding = 'md', elevated = false }: CardProps) {
  return (
    <div
      className={cn(
        'bg-bg2 border border-border-faint rounded-[12px]',
        '[box-shadow:var(--card-shadow)]',
        paddingMap[padding],
        elevated && 'shadow-panel',
        className,
      )}
    >
      {children}
    </div>
  )
}
