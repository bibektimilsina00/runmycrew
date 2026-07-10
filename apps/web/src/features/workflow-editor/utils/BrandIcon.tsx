import { useState, type CSSProperties } from 'react'

/**
 * Brand-icon renderer. Icons are served by the backend from the node system:
 * drop a `<slug>.svg` in `node_system/icons/` (or colocated in a node folder)
 * and `GET /api/v1/icons/<slug>` serves it — no frontend change, no registry.
 *
 * There is no CDN fallback: a slug with no local SVG renders a blank tile.
 * `<slug>` is a node's lowercase `icon` or a provider's `icon_slug`.
 *
 * Rendered as `<img>` (not inline SVG) so the browser handles caching / lazy
 * loading / failure. Trade-off: CSS can't recolour it — ship the full-colour
 * variant onto a neutral tile (the modern look: Linear / Figma / n8n).
 */
const ICON_BASE = `${import.meta.env.VITE_API_URL || '/api/v1'}/icons`

interface BrandIconProps {
  slug: string
  /** Forwarded to the underlying `<img>`. Matches the Lucide-icon
   *  contract — `getIcon()` consumers `React.cloneElement` the result
   *  with a `size-[Npx]` class to size it, so we have to honour that. */
  className?: string
  /** Forwarded inline style. Use when the size needs to be an exact
   *  pixel value computed at render time (Tailwind arbitrary values
   *  like `w-[12px]` only work for static strings the scanner sees). */
  style?: CSSProperties
  /**
   * Optional fallback text shown when the icon fails to load (missing SVG).
   * Usually the first letter of the brand name. When omitted, we derive it
   * from the slug so cards never render as a blank tile.
   */
  fallbackLabel?: string
}

export function BrandIcon({ slug, className, style, fallbackLabel }: BrandIconProps) {
  const [errored, setErrored] = useState(false)
  if (errored) {
    const letter = (fallbackLabel ?? slug).replace(/[^a-zA-Z0-9]/g, '')[0] ?? '?'
    return (
      <span
        className={
          className
            ? `${className} inline-flex items-center justify-center bg-white/5 text-text-mute font-semibold`
            : 'inline-flex items-center justify-center bg-white/5 text-text-mute font-semibold'
        }
        style={style}
        title={fallbackLabel ?? slug}
      >
        {letter.toUpperCase()}
      </span>
    )
  }
  return (
    <img
      src={`${ICON_BASE}/${slug.toLowerCase()}`}
      alt={fallbackLabel ?? slug}
      loading="lazy"
      decoding="async"
      className={className ?? 'object-contain'}
      style={style}
      onError={() => setErrored(true)}
    />
  )
}
