import { useState, type CSSProperties } from 'react'

/**
 * Brand-icon CDN. jsDelivr fronts theSVG's GitHub repo on a global
 * edge network — sub-100ms TTFB, CORS-open, aggressive cache headers.
 * Using `@main` keeps us auto-updating to whatever icons theSVG adds.
 *
 * Why `<img>` instead of inline SVG via fetch+injection? The browser
 * already does what we'd build by hand: HTTP caching, lazy loading,
 * failure handling. The trade-off is that we can't recolour the
 * loaded SVG via CSS — so we ship the `default` (full-colour) variant
 * onto a neutral tile background. That's also the modern look
 * (Linear / Figma / n8n) — the brand identity comes from the logo,
 * not a tinted tile beneath it.
 */
const CDN_BASE = 'https://cdn.jsdelivr.net/gh/glincker/thesvg@main/public/icons'

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
}

export function BrandIcon({ slug, className, style }: BrandIconProps) {
  const [errored, setErrored] = useState(false)
  if (errored) {
    return <span className={className ?? 'inline-block'} style={style} />
  }
  return (
    <img
      src={`${CDN_BASE}/${slug}/default.svg`}
      alt={slug}
      loading="lazy"
      decoding="async"
      className={className ?? 'object-contain'}
      style={style}
      onError={() => setErrored(true)}
    />
  )
}
