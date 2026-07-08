'use client'

import { type ReactNode } from 'react'
import { cn } from '@/lib/cn'

interface BentoGridProps {
  children: ReactNode
  className?: string
}

/**
 * BentoGrid — responsive asymmetric grid layout.
 * Children should be `<BentoCard>` components.
 * Adapted from Aceternity UI for RunMyCrew dashboard layouts.
 */
function BentoGrid({ children, className }: BentoGridProps) {
  return (
    <div
      className={cn(
        'grid auto-rows-[minmax(160px,auto)] grid-cols-3 gap-4',
        'max-lg:grid-cols-2 max-sm:grid-cols-1',
        className,
      )}
    >
      {children}
    </div>
  )
}

interface BentoCardProps {
  children: ReactNode
  className?: string
  /** Span columns (1–3). */
  colSpan?: 1 | 2 | 3
  /** Span rows (1–2). */
  rowSpan?: 1 | 2
  /** Enable mouse-tracking spotlight. */
  spotlight?: boolean
  href?: string
}

/**
 * BentoCard — a single cell in the bento grid layout.
 */
function BentoCard({
  children,
  className,
  colSpan = 1,
  rowSpan = 1,
  spotlight = false,
}: BentoCardProps) {
  const colSpanClass = {
    1: 'col-span-1',
    2: 'col-span-2',
    3: 'col-span-3',
  }[colSpan]

  const rowSpanClass = {
    1: 'row-span-1',
    2: 'row-span-2',
  }[rowSpan]

  return (
    <div
      className={cn(
        'group relative flex flex-col overflow-hidden',
        'rounded-[14px] border border-border-faint bg-bg',
        'p-5 transition-[border-color,transform] [transition-duration:200ms]',
        'hover:border-border-soft',
        colSpanClass,
        rowSpanClass,
        className,
      )}
    >
      {spotlight && (
        <BentoSpotlight />
      )}
      {children}
    </div>
  )
}

/** Internal spotlight that follows the group hover state. */
function BentoSpotlight() {
  return (
    <div
      className={cn(
        'pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100',
        'transition-opacity duration-300',
      )}
      style={{
        background:
          'radial-gradient(400px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), var(--accent), transparent 40%)',
        opacity: 0.06,
      }}
    />
  )
}

export { BentoGrid, BentoCard }
