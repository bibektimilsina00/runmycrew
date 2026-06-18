import type { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

/**
 * Page-level horizontal container — every marketing surface uses the same
 * max-width + gutters so the rhythm stays consistent. Override by passing
 * `className`; the base classes can be safely extended.
 */
export function Container({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'mx-auto w-full max-w-[1160px] px-6 sm:px-8 lg:px-10',
        className,
      )}
      {...props}
    />
  )
}
