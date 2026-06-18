/**
 * Static docs navigation tree. When swapping in Fumadocs (or MDX +
 * frontmatter) keep this shape so the sidebar component doesn't have
 * to change — only the source of truth moves.
 */

export type DocLeaf = {
  title: string
  slug: string
  /** Stub body for placeholder pages until MDX lands. */
  intro?: string
}

export type DocGroup = {
  group: string
  items: DocLeaf[]
}

export const DOCS_NAV: DocGroup[] = [
  {
    group: 'Get started',
    items: [
      { slug: '',              title: 'Introduction', intro: 'Welcome to Fuse — the automation system for teams and agents.' },
      { slug: 'quickstart',    title: 'Quickstart',   intro: 'Build your first workflow in under 5 minutes.' },
      { slug: 'concepts',      title: 'Core concepts', intro: 'Triggers, conditions, actions, and the execution model.' },
      { slug: 'glossary',      title: 'Glossary' },
    ],
  },
  {
    group: 'Building workflows',
    items: [
      { slug: 'fuse-ai',       title: 'Fuse AI',      intro: 'Generate workflows from a single prompt.' },
      { slug: 'triggers',      title: 'Triggers' },
      { slug: 'conditions',    title: 'Conditions' },
      { slug: 'actions',       title: 'Actions' },
      { slug: 'templates',     title: 'Templates' },
    ],
  },
  {
    group: 'Connections',
    items: [
      { slug: 'oauth',         title: 'OAuth integrations' },
      { slug: 'webhooks',      title: 'Webhooks' },
      { slug: 'custom-apps',   title: 'Custom apps' },
      { slug: 'api-keys',      title: 'API keys' },
    ],
  },
  {
    group: 'Run & observe',
    items: [
      { slug: 'scheduling',    title: 'Scheduling' },
      { slug: 'retries',       title: 'Retries' },
      { slug: 'run-history',   title: 'Run history' },
      { slug: 'alerts',        title: 'Alerts' },
      { slug: 'replay',        title: 'Run replay' },
    ],
  },
  {
    group: 'Self-hosting',
    items: [
      { slug: 'self-host',     title: 'Self-host overview' },
      { slug: 'docker',        title: 'Docker compose' },
      { slug: 'env',           title: 'Environment reference' },
      { slug: 'backup',        title: 'Backup & restore' },
    ],
  },
  {
    group: 'API',
    items: [
      { slug: 'api/auth',      title: 'Authentication' },
      { slug: 'api/workflows', title: 'Workflows' },
      { slug: 'api/runs',      title: 'Runs' },
    ],
  },
]

/** Flat helper for slug lookups. */
export function findDoc(slugPath: string[]): { group: string; leaf: DocLeaf } | null {
  const target = slugPath.join('/')
  for (const g of DOCS_NAV) {
    for (const leaf of g.items) {
      if (leaf.slug === target) return { group: g.group, leaf }
    }
  }
  return null
}
