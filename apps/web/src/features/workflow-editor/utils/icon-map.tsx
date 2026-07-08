import React from 'react'
import * as LucideIcons from 'lucide-react'
import { BrandIcon } from './BrandIcon'

/**
 * Two-tier icon resolver:
 *
 * 1. **theSVG brand mark.** Anything lowercase / kebab-case
 *    (`youtube`, `google-sheets`, `slack`) is fetched on demand from
 *    `https://thesvg.org/icons/<slug>/<variant>.svg`. No registry,
 *    no static imports — backend names a slug, browser hits the CDN,
 *    response is cached for the session.
 * 2. **Lucide.** Anything PascalCase (`Play`, `Clock`, `MessageSquare`)
 *    is a bundled Lucide icon.
 *
 * The split-by-casing rule means we never burn a network request on
 * a Lucide name pretending to be a theSVG slug, and we never miss a
 * brand because someone forgot to register it.
 *
 * If the slug is unknown to theSVG, `BrandIcon` renders a transparent
 * placeholder of the same size and the negative result is cached so
 * the editor doesn't keep banging on the CDN.
 */
export const getIcon = (iconName: string): React.ReactNode => {
  if (looksLikeBrandSlug(iconName)) {
    return <BrandIcon slug={iconName.toLowerCase()} />
  }
  const LucideComponent = (LucideIcons as unknown as Record<string, React.ElementType | undefined>)[iconName]
  if (LucideComponent) {
    return <LucideComponent />
  }
  return <LucideIcons.Globe />
}

/** A brand slug is all-lowercase letters / digits, optionally
 *  hyphen- or underscore-separated (`microsoft_teams`, `google_ads`,
 *  `google-sheets`). Lucide names are PascalCase, so an uppercase
 *  first letter is a perfect signal that this is NOT a brand. */
function looksLikeBrandSlug(name: string): boolean {
  if (!name) return false
  return /^[a-z0-9]+(?:[-_][a-z0-9]+)*$/.test(name)
}
