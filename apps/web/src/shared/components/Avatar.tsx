import { useState } from 'react'
import { cn } from '@/lib/cn'

type AvatarSize = 'sm' | 'md' | 'lg'

interface AvatarProps {
  name?: string
  src?: string
  fallback?: string
  size?: AvatarSize
  className?: string
}

const sizeMap: Record<AvatarSize, { wrapper: string; text: string }> = {
  sm: { wrapper: 'w-[22px] h-[22px] rounded-[5px] text-[10px]', text: '' },
  md: { wrapper: 'w-[26px] h-[26px] rounded-[7px] text-[11px]', text: '' },
  lg: { wrapper: 'w-[32px] h-[32px] rounded-[8px] text-[13px]', text: '' },
}

export function Avatar({ name, src, fallback, size = 'md', className }: AvatarProps) {
  const { wrapper } = sizeMap[size]
  const [imgError, setImgError] = useState(false)
  const displayName = name || fallback || '?'
  const letter = displayName.trim().charAt(0).toUpperCase()

  const showImage = src && !imgError

  return (
    <div
      className={cn(
        'inline-flex items-center justify-center shrink-0 select-none overflow-hidden relative',
        'bg-text text-bg font-semibold tracking-[-0.02em]',
        wrapper,
        className,
      )}
    >
      {showImage ? (
        <img
          src={src}
          alt={displayName}
          className="absolute inset-0 w-full h-full object-cover"
          onError={() => setImgError(true)}
        />
      ) : (
        <span>{letter}</span>
      )}
    </div>
  )
}
