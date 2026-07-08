'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/cn'

interface TooltipItem {
  id: string | number
  name: string
  /** Avatar URL or initials fallback. */
  image?: string
  initials?: string
  designation?: string
}

interface AnimatedTooltipProps {
  items: TooltipItem[]
  className?: string
}

/**
 * AnimatedTooltip — stacked avatar row with animated tooltip cards on hover.
 * Adapted from Aceternity UI for RunMyCrew.
 * @example
 * ```tsx
 * <AnimatedTooltip items={[{ id: 1, name: 'Alice', initials: 'AL', designation: 'Admin' }]} />
 * ```
 */
function AnimatedTooltip({ items, className }: AnimatedTooltipProps) {
  const [hoveredId, setHoveredId] = useState<string | number | null>(null)

  return (
    <div className={cn('flex flex-row items-center', className)}>
      {items.map((item) => (
        <div
          key={item.id}
          className="relative -ml-2 first:ml-0 group"
          onMouseEnter={() => setHoveredId(item.id)}
          onMouseLeave={() => setHoveredId(null)}
        >
          <AnimatePresence>
            {hoveredId === item.id && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.9 }}
                animate={{ opacity: 1, y: -6, scale: 1 }}
                exit={{ opacity: 0, y: 6, scale: 0.95 }}
                transition={{ type: 'spring', stiffness: 260, damping: 20 }}
                className={cn(
                  'absolute -top-16 left-1/2 -translate-x-1/2 z-50',
                  'px-3 py-2 rounded-[8px] min-w-max',
                  'bg-surface border border-border-faint shadow-dropdown',
                  'flex flex-col items-center gap-0.5',
                )}
              >
                <span className="text-xs font-medium text-text whitespace-nowrap">{item.name}</span>
                {item.designation && (
                  <span className="text-xs text-text-faint whitespace-nowrap">{item.designation}</span>
                )}
                {/* Arrow */}
                <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 rotate-45 bg-surface border-r border-b border-border-faint" />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Avatar */}
          <div
            className={cn(
              'relative w-8 h-8 rounded-full border-2 border-bg overflow-hidden',
              'bg-surface-2 flex items-center justify-center',
              'cursor-pointer transition-transform [transition-duration:150ms] group-hover:z-10 group-hover:scale-110',
            )}
          >
            {item.image ? (
              <img
                src={item.image}
                alt={item.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-xs font-semibold text-text-mute">
                {item.initials ?? item.name.slice(0, 2).toUpperCase()}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export { AnimatedTooltip, type TooltipItem }
