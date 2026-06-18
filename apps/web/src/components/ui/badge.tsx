import { type HTMLAttributes } from 'react'
import { cn } from '@/lib/cn'
import { badgeVariants, type BadgeVariantProps } from './badge.variants'

export interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
    BadgeVariantProps {}

/**
 * Fuse Badge — CVA-based status / label chips.
 */
function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge }

