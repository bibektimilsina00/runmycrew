import React from 'react'
import { Icon as IconifyIcon } from '@iconify/react'
import * as LucideIcons from 'lucide-react'

/**
 * Two icon registries, one entry point.
 *
 * - **Iconify-prefixed names** (anything containing `:`, e.g. `si:youtube`,
 *   `mdi:home`) load on-demand from the Iconify CDN and cache in
 *   localStorage. That's where every integration node's brand icon
 *   comes from — Simple Icons via the `si:` prefix.
 * - **Bare names** fall through to lucide-react, which is bundled into
 *   the SPA. Used for trigger / logic / UI nodes (`Play`, `Clock`,
 *   `Database`, etc).
 *
 * Backend node metadata spells brand icons in react-icons casing
 * (`si:SiYoutube`, `si:SiGooglesheets`), but Iconify's Simple Icons
 * collection uses kebab-case slugs (`youtube`, `google-sheets`).
 * `SI_BRAND_ALIASES` maps the names we actually ship to the slugs
 * Iconify expects so we don't have to rewrite every node's metadata.
 */
export const getIcon = (iconName: string): React.ReactNode => {
  if (iconName.includes(':')) {
    return <IconifyIcon icon={normaliseIconifyName(iconName)} />
  }
  const Component =
    (LucideIcons as unknown as Record<string, React.ElementType>)[iconName] ??
    LucideIcons.Globe
  return <Component />
}

/**
 * Curated map of react-icons-style identifiers → Simple Icons slug.
 * Listed explicitly because the lossy "lowercase Si<brand>" form
 * backend uses can't be deterministically un-mashed back to its
 * compound kebab form (`Googlesheets` could in theory be `goog-le-sheets`).
 * Add an entry here whenever a new integration ships.
 */
const SI_BRAND_ALIASES: Record<string, string> = {
  airtable: 'airtable',
  discord: 'discord',
  github: 'github',
  gmail: 'gmail',
  googleanalytics: 'googleanalytics',
  googlecalendar: 'googlecalendar',
  googlechat: 'googlechat',
  googlecloudstorage: 'googlecloud',
  googlecontacts: 'googlecontacts',
  googledocs: 'googledocs',
  googledrive: 'googledrive',
  googleforms: 'googleforms',
  googlesearchconsole: 'googlesearchconsole',
  googlesheets: 'googlesheets',
  googleslides: 'googleslides',
  googletasks: 'googletasks',
  hubspot: 'hubspot',
  jira: 'jira',
  linear: 'linear',
  mongodb: 'mongodb',
  mysql: 'mysql',
  neo: 'neo4j',
  notion: 'notion',
  perplexity: 'perplexity',
  postgresql: 'postgresql',
  salesforce: 'salesforce',
  slack: 'slack',
  stripe: 'stripe',
  telegram: 'telegram',
  youtube: 'youtube',
  // Common aliases other folders may use as the integration evolves.
  google: 'google',
  meta: 'meta',
  anthropic: 'anthropic',
  openai: 'openai',
}

function normaliseIconifyName(raw: string): string {
  const colon = raw.indexOf(':')
  if (colon === -1) return raw
  const prefix = raw.slice(0, colon)
  let tail = raw.slice(colon + 1)
  // Strip react-icons' `Si` prefix on Simple-Icons slugs so the lookup
  // sees `youtube` / `googlesheets` rather than `siYoutube` /
  // `siGooglesheets`.
  if (prefix === 'si' && tail.startsWith('Si') && tail.length > 2 && tail[2] === tail[2].toUpperCase()) {
    tail = tail.slice(2)
  }
  const lowered = tail.toLowerCase()
  if (prefix === 'si' && SI_BRAND_ALIASES[lowered]) {
    return `simple-icons:${SI_BRAND_ALIASES[lowered]}`
  }
  // Best-effort kebab-case for anything not in the alias table — keeps
  // `mdi:HomeAccount` -> `mdi:home-account` working too.
  const kebab = tail
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1-$2')
    .toLowerCase()
  return `${prefix}:${kebab}`
}
