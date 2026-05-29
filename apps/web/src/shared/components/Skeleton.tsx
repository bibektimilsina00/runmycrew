import { type CSSProperties } from 'react'
import { cn } from '@/lib/cn'

interface SkeletonProps {
  className?: string
  rounded?: 'sm' | 'md' | 'full'
  style?: CSSProperties
}

export function Skeleton({ className, rounded = 'sm', style }: SkeletonProps) {
  return (
    <div
      style={style}
      className={cn(
        'bg-surface-2 animate-pulse',
        rounded === 'sm'   && 'rounded-[6px]',
        rounded === 'md'   && 'rounded-md',
        rounded === 'full' && 'rounded-full',
        className,
      )}
    />
  )
}

// Preset compositions
export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn('flex flex-col gap-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className="h-3"
          style={{ width: i === lines - 1 ? '60%' : '100%' } as React.CSSProperties}
        />
      ))}
    </div>
  )
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('bg-bg2 border border-border-faint rounded-md p-4 flex gap-3', className)}>
      <Skeleton rounded="md" className="w-9 h-9 shrink-0" />
      <div className="flex flex-col gap-2 flex-1 min-w-0 justify-center">
        <Skeleton className="h-3 w-2/3" />
        <Skeleton className="h-2.5 w-1/3" />
      </div>
    </div>
  )
}
