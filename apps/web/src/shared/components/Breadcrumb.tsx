import { type ReactNode } from 'react'
import { ChevronRight } from 'lucide-react'
import { cn } from '@/lib/cn'

export interface BreadcrumbItem {
  label: string
  href?: string
  icon?: ReactNode
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumb({ items, className }: BreadcrumbProps) {
  return (
    <nav className={cn('flex items-center gap-1', className)} aria-label="Breadcrumb">
      {items.map((item, i) => {
        const isLast = i === items.length - 1
        return (
          <span key={i} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={12} className="text-text-dim shrink-0" />}
            {item.href && !isLast ? (
              <a
                href={item.href}
                className="flex items-center gap-1.5 text-xs text-text-faint hover:text-text-mute transition-colors"
              >
                {item.icon && <span className="[&_svg]:w-3 [&_svg]:h-3">{item.icon}</span>}
                {item.label}
              </a>
            ) : (
              <span className={cn(
                'flex items-center gap-1.5 text-xs',
                isLast ? 'text-text font-medium' : 'text-text-faint',
              )}>
                {item.icon && <span className="[&_svg]:w-3 [&_svg]:h-3">{item.icon}</span>}
                {item.label}
              </span>
            )}
          </span>
        )
      })}
    </nav>
  )
}
