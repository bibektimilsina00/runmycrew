import { cn } from '@/lib/cn'

type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg'

interface SpinnerProps {
  size?: SpinnerSize
  className?: string
}

const sizeMap: Record<SpinnerSize, string> = {
  xs: 'w-3 h-3',    // 12px
  sm: 'w-4 h-4',    // 16px
  md: 'w-5 h-5',    // 20px
  lg: 'w-7 h-7',    // 28px
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <div
      className={cn(
        'shrink-0 rounded-full border-2 border-border-faint border-t-text-mute animate-spin',
        sizeMap[size],
        className,
      )}
    />
  )
}
