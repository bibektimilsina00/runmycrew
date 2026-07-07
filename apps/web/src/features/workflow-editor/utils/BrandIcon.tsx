import { useState, type CSSProperties } from 'react'

/**
 * Brand-icon renderer with a hand-curated local override.
 *
 * Resolution order:
 *  1. **Local SVG** — a file in `src/assets/brand-icons/<slug>.svg`.
 *     Bundled at build time via `import.meta.glob`, so the filename is
 *     the key — no registry to edit. Local always wins (that's the point:
 *     curate the brands you care about).
 *  2. **theSVG CDN** — jsDelivr fronts theSVG's GitHub repo on a global
 *     edge network for slugs with no local file. `@main` auto-updates.
 *  3. **Blank tile** — if both miss.
 *
 * Why `<img>` instead of inline SVG? The browser already does HTTP
 * caching, lazy loading, and failure handling for us. Trade-off: we can't
 * recolour the loaded SVG via CSS, so we ship the full-colour variant onto
 * a neutral tile — also the modern look (Linear / Figma / n8n).
 */
const CDN_BASE = 'https://cdn.jsdelivr.net/gh/glincker/thesvg@main/public/icons'

// Compile-time map of the hand-curated overrides. Drop `<slug>.svg` into
// src/assets/brand-icons/ (slug = provider icon_slug or a node's lowercase
// icon name) and it takes precedence over the CDN. See that folder's README.
const localModules = import.meta.glob('/src/assets/brand-icons/*.svg', {
  eager: true,
  query: '?url',
  import: 'default',
}) as Record<string, string>

const LOCAL_ICONS: Record<string, string> = {}
for (const [path, url] of Object.entries(localModules)) {
  const slug = path.split('/').pop()?.replace(/\.svg$/i, '').toLowerCase()
  if (slug) LOCAL_ICONS[slug] = url
}

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
  const local = LOCAL_ICONS[slug.toLowerCase()]
  const src = local ?? `${CDN_BASE}/${slug}/default.svg`
  return (
    <img
      src={src}
      alt={slug}
      loading="lazy"
      decoding="async"
      className={className ?? 'object-contain'}
      style={style}
      onError={() => setErrored(true)}
    />
  )
}
