import { useState, type ReactNode } from 'react'
import { cn } from '@/lib/cn'

type Side = 'top' | 'bottom' | 'left' | 'right'

interface TooltipProps {
  content: string
  children: ReactNode
  side?: Side
  className?: string
}

const sideStyles: Record<Side, string> = {
  top:    'bottom-full mb-1.5 left-1/2 -translate-x-1/2',
  bottom: 'top-full mt-1.5 left-1/2 -translate-x-1/2',
  left:   'right-full mr-1.5 top-1/2 -translate-y-1/2',
  right:  'left-full ml-1.5 top-1/2 -translate-y-1/2',
}

export function Tooltip({ content, children, side = 'top', className }: TooltipProps) {
  const [visible, setVisible] = useState(false)

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      <span
        className={cn(
          'absolute z-50 pointer-events-none',
          'px-2.5 py-1.5',
          'bg-surface-3 border border-border shadow-float',
          'text-xs text-text-mute',
          'rounded-[6px] max-w-xs whitespace-normal break-words',
          'transition-all duration-200',
          sideStyles[side],
          visible ? 'opacity-100 scale-100' : 'opacity-0 scale-95',
          className,
        )}
      >
        {content}
      </span>
    </span>
  )
}
