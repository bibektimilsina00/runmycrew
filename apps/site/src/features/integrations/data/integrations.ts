/**
 * Integration catalog. Mirrors the providers actually supported in the
 * Fuse product so the marketing page never lies. When adding a real
 * connector, append it here — letters render as the icon tile.
 */

export type IntegrationCategory =
  | 'Communication'
  | 'Developer'
  | 'Productivity'
  | 'Marketing'
  | 'Finance'
  | 'Storage'
  | 'AI'

export type Integration = {
  slug: string
  name: string
  category: IntegrationCategory
  description: string
  /** 2-letter mono tile. */
  letter: string
  /** Solid bg behind the tile letter. */
  color: string
}

export const INTEGRATION_CATEGORIES: IntegrationCategory[] = [
  'Communication',
  'Developer',
  'Productivity',
  'Marketing',
  'Finance',
  'Storage',
  'AI',
]

export const INTEGRATIONS: Integration[] = [
  // Communication
  { slug: 'slack',       name: 'Slack',       category: 'Communication', description: 'Messages, channels & DMs.',     letter: 'SL', color: '#4a154b' },
  { slug: 'gmail',       name: 'Gmail',       category: 'Communication', description: 'Send & search Gmail messages.', letter: 'GM', color: '#ea4335' },
  { slug: 'google-chat', name: 'Google Chat', category: 'Communication', description: 'Spaces and direct messages.',   letter: 'GC', color: '#1a73e8' },
  // Developer
  { slug: 'github',      name: 'GitHub',      category: 'Developer', description: 'Issues, PRs and Actions.',          letter: 'GH', color: '#24292f' },
  { slug: 'linear',      name: 'Linear',      category: 'Developer', description: 'Issues, projects and cycles.',      letter: 'LN', color: '#5e6ad2' },
  { slug: 'jira',        name: 'Jira',        category: 'Developer', description: 'Tickets, sprints and boards.',      letter: 'JR', color: '#2684ff' },
  // Productivity
  { slug: 'notion',      name: 'Notion',      category: 'Productivity', description: 'Databases, pages and blocks.',   letter: 'NO', color: '#111' },
  { slug: 'gdocs',       name: 'Google Docs', category: 'Productivity', description: 'Read, write and append docs.',   letter: 'GD', color: '#4285f4' },
  { slug: 'gsheets',     name: 'Google Sheets', category: 'Productivity', description: 'Rows, ranges and pivot ops.',  letter: 'GS', color: '#0f9d58' },
  { slug: 'gslides',     name: 'Google Slides', category: 'Productivity', description: 'Generate decks from data.',    letter: 'SL', color: '#fbbc04' },
  { slug: 'gcalendar',   name: 'Google Calendar', category: 'Productivity', description: 'Events, invites and busy.',  letter: 'CA', color: '#4285f4' },
  // Marketing
  { slug: 'meta',        name: 'Meta',        category: 'Marketing', description: 'Ads, lead forms and Pages.',         letter: 'MT', color: '#0866ff' },
  { slug: 'gsc',         name: 'Search Console', category: 'Marketing', description: 'Queries, pages and sitemaps.',    letter: 'GS', color: '#458cf7' },
  { slug: 'ga4',         name: 'GA4',          category: 'Marketing', description: 'Reports and properties.',           letter: 'G4', color: '#e67c2f' },
  // Finance
  { slug: 'stripe',      name: 'Stripe',      category: 'Finance', description: 'Payments, refunds and disputes.',     letter: 'ST', color: '#635bff' },
  // Storage
  { slug: 'gdrive',      name: 'Google Drive', category: 'Storage', description: 'Upload, move and share files.',      letter: 'GD', color: '#fbbc04' },
  { slug: 'gcs',         name: 'Cloud Storage', category: 'Storage', description: 'Buckets, objects and ACLs.',         letter: 'CS', color: '#4285f4' },
  // AI
  { slug: 'claude',      name: 'Anthropic',    category: 'AI', description: 'Claude models inside any workflow.',      letter: 'AN', color: '#cc785c' },
  { slug: 'openai',      name: 'OpenAI',       category: 'AI', description: 'GPT models for prompts and embeddings.',   letter: 'OA', color: '#10a37f' },
]

export function integrationsByCategory(cat: IntegrationCategory): Integration[] {
  return INTEGRATIONS.filter((i) => i.category === cat)
}
