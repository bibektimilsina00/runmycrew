'use client'

import { useRef, useState } from 'react'
import { cn } from '@/lib/cn'

interface SpotlightCardProps {
  children: React.ReactNode
  className?: string
  /** Spotlight color — defaults to accent (muted indigo glow). */
  spotlightColor?: string
}

/**
 * SpotlightCard — a card that follows the mouse with a soft spotlight glow.
 * Adapted from Aceternity UI for RunMyCrew design system.
 */
function SpotlightCard({ children, className, spotlightColor }: SpotlightCardProps) {
  const divRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [opacity, setOpacity] = useState(0)

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!divRef.current) return
    const rect = divRef.current.getBoundingClientRect()
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }

  const color = spotlightColor ?? 'var(--accent)'

  return (
    <div
      ref={divRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setOpacity(1)}
      onMouseLeave={() => setOpacity(0)}
      className={cn(
        'relative overflow-hidden rounded-[12px] border border-border-faint bg-bg',
        'transition-[border-color] [transition-duration:200ms] hover:border-border-soft',
        className,
      )}
    >
      {/* Spotlight gradient layer */}
      <div
        className="pointer-events-none absolute inset-0 transition-opacity duration-300"
        style={{
          opacity,
          background: `radial-gradient(600px circle at ${position.x}px ${position.y}px, ${color}18, transparent 40%)`,
        }}
      />
      {children}
    </div>
  )
}

export { SpotlightCard }
