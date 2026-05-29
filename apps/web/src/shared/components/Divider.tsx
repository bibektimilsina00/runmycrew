import { cn } from '@/lib/cn'

interface DividerProps {
  className?: string
  vertical?: boolean
}

export function Divider({ className, vertical }: DividerProps) {
  if (vertical) {
    return (
      <div
        className={cn('w-px bg-border-faint self-stretch shrink-0', className)}
      />
    )
  }
  return (
    <div
      className={cn('h-px w-full bg-border-faint shrink-0', className)}
    />
  )
}
