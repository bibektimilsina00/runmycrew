import { Icons } from '@/shared/components/icons'

interface AppLogoProps {
  /** Owner-provided logo URL (config.logo_url). Falls back to the brand mark. */
  src?: string | null
  size?: number
  className?: string
}

/** App identity mark used across the hosted page — header, welcome hero,
 *  assistant avatars. Owner logo when configured, RunMyCrew mark otherwise. */
export function AppLogo({ src, size = 28, className }: AppLogoProps) {
  if (src) {
    return (
      <img
        src={src}
        alt=""
        width={size}
        height={size}
        className={`rounded-[8px] object-cover ${className ?? ''}`}
        style={{ width: size, height: size }}
      />
    )
  }
  return (
    <span
      className={`flex items-center justify-center rounded-[8px] ${className ?? ''}`}
      style={{
        width: size,
        height: size,
        background: 'color-mix(in oklab, var(--app-accent, #8b5cf6) 16%, transparent)',
        color: 'var(--app-accent, #8b5cf6)',
      }}
    >
      <Icons.BrandMark style={{ width: size * 0.62, height: size * 0.62 }} />
    </span>
  )
}
