/**
 * Single source of truth for every word + tile rendered on the marketing
 * landing page. Components stay presentational and import only from here.
 */

export type NavMenuKey = 'docs' | 'blog'
export type NavLink = { label: string; href: string; menu?: NavMenuKey }
export const NAV_LINKS: NavLink[] = [
  { label: 'Docs',         href: '/docs', menu: 'docs' },
  { label: 'Blog',         href: '/blog', menu: 'blog' },
  { label: 'Integrations', href: '/integrations' },
  { label: 'Templates',    href: '/templates' },
  { label: 'Pricing',      href: '/pricing' },
]

/* ─── Nav-menu popups (Docs + Blog) ───────────────────────────────── */

export type NavHeroCard = {
  title: string
  href: string
  /** SVG node rendered inside the dark preview area at the top of the card. */
  visual: 'workflow' | 'chart' | 'logs' | 'enterprise'
}

export type NavMiniCard = {
  icon: 'sparkles' | 'plug' | 'server' | 'shield' | 'bot' | 'cog'
  title: string
  sub: string
  href: string
}

export type NavThumbCard = {
  title: string
  visual: 'city' | 'graph' | 'collab' | 'series' | 'features'
  href: string
}

/** Docs popup — 2 hero cards on top, 3 mini-cards underneath. */
export const NAV_MENU_DOCS = {
  hero: [
    { title: 'Introduction', href: '/docs',            visual: 'workflow' },
    { title: 'Quickstart',   href: '/docs/quickstart', visual: 'chart'    },
  ] as NavHeroCard[],
  mini: [
    { icon: 'sparkles', title: 'Crew AI',     sub: 'Prompt → workflow',  href: '/docs/crew-ai'   },
    { icon: 'plug',     title: 'Connections', sub: 'OAuth & webhooks',    href: '/docs/oauth'     },
    { icon: 'server',   title: 'Self-hosting', sub: 'Run on your infra',  href: '/docs/self-host' },
  ] as NavMiniCard[],
}

/** Blog popup — 1 large featured + 1 enterprise card + 3 thumb cards. */
export const NAV_MENU_BLOG = {
  featured:   { title: 'Introducing Crew AI',   href: '/blog/introducing-crew-ai', visual: 'city' as const },
  enterprise: { title: 'RunMyCrew for Enterprise',    href: '/blog/enterprise',          visual: 'enterprise' as const },
  thumbs: [
    { title: 'Series Seed announcement',  visual: 'series', href: '/blog/seed-announcement'     },
    { title: 'Realtime collaboration',    visual: 'collab', href: '/blog/realtime-collaboration' },
    { title: 'Inside the RunMyCrew executor',  visual: 'graph',  href: '/blog/inside-the-executor'   },
  ] as NavThumbCard[],
}

/* ─── HERO ─────────────────────────────────────────────────────────── */

export const HERO = {
  title: 'The automation system for teams and agents',
  subtitle: 'Connect every app you already use — no glue code required.',
  releaseNote: { label: 'New', target: 'Crew AI' },
} as const

/** Compact recent-runs list rendered inside the dashboard hero mockup. */
export type HeroRun = { name: string; trigger: string; dur: string; ago: string }
export const HERO_RUNS: HeroRun[] = [
  { name: 'Daily standup digest',  trigger: 'Schedule', dur: '1.2s', ago: '9:00' },
  { name: 'Urgent issue → Slack',  trigger: 'Webhook',  dur: '0.4s', ago: '8:41' },
  { name: 'New lead → Notion CRM', trigger: 'Meta',     dur: '0.9s', ago: '8:32' },
]

/** Three "Suggested automations" cards under the prompt — mirrors the
 *  real RunMyCrew dashboard's empty-state suggestion strip. */
export type HeroSuggestion = { icon: string; iconBg: string; title: string }
export const HERO_SUGGESTIONS: HeroSuggestion[] = [
  {
    icon: 'EV',
    iconBg: 'linear-gradient(135deg,#5e6ad2,#404ab1)',
    title: 'Every weekday at 9am, summarize new GitHub issues and post to Slack',
  },
  {
    icon: 'WH',
    iconBg: 'linear-gradient(135deg,#4cc38a,#2f9a64)',
    title: 'When a new row is added to Notion, send a welcome email',
  },
  {
    icon: 'FE',
    iconBg: 'linear-gradient(135deg,#e5675f,#b94840)',
    title: 'Fetch JSON from an API and save it to a database',
  },
]

/** Dashboard-mockup sidebar entries inside the hero product shot. */
export type SideTopEntry = { label: string; dot: string; active?: boolean; count?: string }
export const HERO_SIDE_TOP: SideTopEntry[] = [
  { label: 'Home',         dot: 'var(--primary)', active: true },
  { label: 'Automations',  dot: '#8b5cf6',        count:  '22' },
  { label: 'Templates',    dot: '#4cc38a' },
]

export type SideConnEntry = { label: string; letter: string; bg: string }
export const HERO_SIDE_CONN: SideConnEntry[] = [
  { label: 'GitHub', letter: 'GH', bg: '#24292f' },
  { label: 'Slack',  letter: 'SL', bg: '#4a154b' },
  { label: 'Google', letter: 'GO', bg: '#1a73e8' },
]

export type HeroMetric = {
  label: string
  value: string
  delta: string
  color: string
  /** Polyline points for a 60x18 viewBox sparkline. */
  spark: string
}
export const HERO_METRICS: HeroMetric[] = [
  { label: 'Runs today',  value: '214',   delta: '+34%',  color: 'var(--chart-2)',         spark: '0,14 8,12 16,15 24,8 32,11 40,5 48,7 60,3' },
  { label: 'Success',     value: '99.2%', delta: '+1.1pp', color: 'var(--chart-2)',        spark: '0,11 8,12 16,10 24,11 32,7 40,8 48,5 60,4' },
  { label: 'Time saved',  value: '18h',   delta: '+2.4h',  color: 'var(--chart-2)',        spark: '0,16 8,14 16,13 24,10 32,11 40,7 48,8 60,4' },
  { label: 'Active',      value: '22',    delta: '+3',     color: 'var(--muted-foreground)', spark: '0,10 8,10 16,11 24,9 32,10 40,9 48,10 60,9' },
]

/* ─── PROMPT EXAMPLES (drive Hero + Build mockup) ──────────────────── */

export type WorkflowNode = {
  kind: 'TRIGGER' | 'FILTER' | 'ACTION' | 'FETCH' | 'AI'
  title: string
  sub: string
  icon: string
  iconBg: string
  slug?: string
  last?: boolean
}

export type PromptExample = {
  label: string
  text: string
  nodes: WorkflowNode[]
}

export const EXAMPLES: PromptExample[] = [
  {
    label: 'Urgent issues → Slack',
    text: 'When a GitHub issue is labeled "urgent", post it to #incidents in Slack and create a Linear ticket.',
    nodes: [
      { kind: 'TRIGGER', title: 'GitHub · Issue labeled', sub: 'label is "urgent"', icon: 'GH', iconBg: '#24292f', slug: 'github' },
      { kind: 'FILTER',  title: 'Only if unassigned',     sub: 'assignee is empty', icon: 'IF', iconBg: '#3a3f4a' },
      { kind: 'ACTION',  title: 'Slack · Post message',   sub: 'channel #incidents', icon: 'SL', iconBg: '#4a154b', slug: 'slack' },
      { kind: 'ACTION',  title: 'Linear · Create issue',  sub: 'team Platform · P1', icon: 'LN', iconBg: '#5e6ad2', slug: 'linear', last: true },
    ],
  },
  {
    label: 'New lead → CRM',
    text: 'When a Meta lead form is submitted, add the lead to Notion and send a welcome email via Gmail.',
    nodes: [
      { kind: 'TRIGGER', title: 'Meta · Lead submitted', sub: 'form "Spring Campaign"', icon: 'MT', iconBg: '#0866ff', slug: 'meta' },
      { kind: 'ACTION',  title: 'Notion · Add to CRM',   sub: 'database Leads',         icon: 'NO', iconBg: '#111', slug: 'notion' },
      { kind: 'ACTION',  title: 'Gmail · Send welcome',   sub: 'template Welcome v2',    icon: 'GM', iconBg: '#ea4335', slug: 'gmail', last: true },
    ],
  },
  {
    label: 'Daily standup digest',
    text: 'Every weekday at 9am, summarize new GitHub activity with AI and post the digest to Slack.',
    nodes: [
      { kind: 'TRIGGER', title: 'Schedule · 9:00 AM',          sub: 'Mon–Fri',         icon: '⏱', iconBg: '#3a3f4a' },
      { kind: 'FETCH',   title: 'GitHub · Recent activity',    sub: 'last 24 hours',   icon: 'GH', iconBg: '#24292f', slug: 'github' },
      { kind: 'AI',      title: 'Crew AI · Summarize',         sub: 'Claude Sonnet',   icon: 'AI', iconBg: '#5e6ad2' },
      { kind: 'ACTION',  title: 'Slack · Post digest',         sub: 'channel #standup', icon: 'SL', iconBg: '#4a154b', slug: 'slack', last: true },
    ],
  },
]

/* ─── LOGO CLOUD ───────────────────────────────────────────────────── */

// name + simple-icons slug (served monochrome via cdn.simpleicons.org).
export const LOGOS = [
  { name: 'GitHub', slug: 'github' },
  { name: 'Slack', slug: 'slack' },
  { name: 'Notion', slug: 'notion' },
  { name: 'Google', slug: 'google' },
  { name: 'Meta', slug: 'meta' },
  { name: 'Stripe', slug: 'stripe' },
  { name: 'Linear', slug: 'linear' },
  { name: 'Figma', slug: 'figma' },
] as const

/* ─── STATEMENT SECTION ────────────────────────────────────────────── */

export const STATEMENT = {
  lead: 'A new kind of automation tool.',
  trail:
    'Purpose-built for modern teams with AI at its core, RunMyCrew sets a new standard for connecting the apps you already run on.',
}

export const STATEMENT_FIGS = [
  { tag: 'FIG 0.2 — TRIGGERS', body: 'Start from an app event, a webhook, or a schedule.' },
  { tag: 'FIG 0.3 — LOGIC',    body: 'Branch, filter and transform without writing glue code.' },
  { tag: 'FIG 0.4 — ACTIONS',  body: 'Fan out to every connected tool in one run.' },
] as const

/* ─── FEATURE SECTIONS (heading + sublinks) ───────────────────────── */

export type FeatureMeta = {
  number: string
  slug: string
  label: string
  heading: string
  body: string
  sublinks: { n: string; label: string }[]
}

export const FEATURES = {
  build: {
    number: '1.0',
    slug: 'build',
    label: 'Build',
    heading: 'Build automations\nby describing them',
    body:
      'Turn a plain-English request into a multi-step workflow. Crew AI maps the triggers, conditions, and actions across every connected app — and shows you exactly what it built.',
    sublinks: [
      { n: '1.1', label: 'Crew AI' },
      { n: '1.2', label: 'Triggers' },
      { n: '1.3', label: 'Conditions' },
      { n: '1.4', label: 'Templates' },
    ],
  },
  connect: {
    number: '2.0',
    slug: 'connect',
    label: 'Connect',
    heading: 'Connect the tools\nyou already use',
    body:
      'Authorize GitHub, Slack, Google, Meta and more in a click — no API keys to babysit. RunMyCrew keeps every connection healthy and reconnects when tokens expire.',
    sublinks: [
      { n: '2.1', label: 'Integrations' },
      { n: '2.2', label: 'OAuth' },
      { n: '2.3', label: 'Webhooks' },
      { n: '2.4', label: 'Custom apps' },
    ],
  },
  run: {
    number: '3.0',
    slug: 'run',
    label: 'Run',
    heading: 'Runs that\nnever miss',
    body:
      'Every execution is logged, retried, and observable. Fire on a schedule, a webhook, or an app event — RunMyCrew handles backoff and alerts the moment anything drifts.',
    sublinks: [
      { n: '3.1', label: 'Scheduling' },
      { n: '3.2', label: 'Retries' },
      { n: '3.3', label: 'Run history' },
      { n: '3.4', label: 'Alerts' },
    ],
  },
  observe: {
    number: '4.0',
    slug: 'observe',
    label: 'Observe',
    heading: 'Understand every\nrun at a glance',
    body:
      'Inspect any run end to end — inputs, outputs, timing, and the exact payload at each step. Search, replay and debug in seconds instead of digging through logs.',
    sublinks: [
      { n: '4.1', label: 'Inspector' },
      { n: '4.2', label: 'Replay' },
      { n: '4.3', label: 'Search' },
      { n: '4.4', label: 'Alerts' },
    ],
  },
} satisfies Record<string, FeatureMeta>

/* ─── INTEGRATIONS GRID ───────────────────────────────────────────── */

export type IntegrationCard = {
  key: string
  name: string
  sub: string
  bg: string
  letter: string
  slug?: string
  defaultConnected: boolean
}

export const INTEGRATIONS: IntegrationCard[] = [
  { key: 'github', name: 'GitHub', sub: 'Issues, PRs, Actions',    bg: '#24292f', letter: 'GH', slug: 'github', defaultConnected: true },
  { key: 'slack',  name: 'Slack',  sub: 'Messages & channels',     bg: '#4a154b', letter: 'SL', slug: 'slack',  defaultConnected: true },
  { key: 'notion', name: 'Notion', sub: 'Databases & pages',       bg: '#111',    letter: 'NO', slug: 'notion', defaultConnected: false },
  { key: 'google', name: 'Google', sub: 'Calendar, Sheets, Mail',  bg: '#1a73e8', letter: 'GO', slug: 'google', defaultConnected: false },
  { key: 'stripe', name: 'Stripe', sub: 'Payments & webhooks',     bg: '#635bff', letter: 'ST', slug: 'stripe', defaultConnected: false },
  { key: 'meta',   name: 'Meta',   sub: 'Ads & lead forms',        bg: '#0866ff', letter: 'MT', slug: 'meta',   defaultConnected: false },
]

/* ─── RECENT RUNS ─────────────────────────────────────────────────── */

export type RecentRun = {
  name: string
  trigger: string
  dur: string
  time: string
  dot: string
  glow: string
}

export const RUNS: RecentRun[] = [
  { name: 'Daily standup digest',     trigger: 'Schedule', dur: '1.2s', time: '9:00', dot: 'var(--chart-2)', glow: 'rgba(76,195,138,0.18)' },
  { name: 'Urgent issue → Slack',     trigger: 'Webhook',  dur: '0.4s', time: '8:41', dot: 'var(--chart-2)', glow: 'rgba(76,195,138,0.18)' },
  { name: 'New lead → Notion CRM',    trigger: 'Meta',     dur: '0.9s', time: '8:32', dot: 'var(--chart-2)', glow: 'rgba(76,195,138,0.18)' },
  { name: 'Stripe refund alert',      trigger: 'Webhook',  dur: '0.3s', time: '8:12', dot: 'var(--chart-2)', glow: 'rgba(76,195,138,0.18)' },
  { name: 'Weekly metrics digest',    trigger: 'Schedule', dur: '2.1s', time: '7:00', dot: 'var(--chart-3)', glow: 'rgba(229,179,65,0.16)' },
  { name: 'Calendar → standup notes', trigger: 'Google',   dur: '0.7s', time: '6:48', dot: 'var(--chart-2)', glow: 'rgba(76,195,138,0.18)' },
]

/* ─── OBSERVE PANE — run-detail steps + payloads ───────────────────── */

export type RunStep = {
  icon: string
  iconBg: string
  slug?: string
  title: string
  ms: string
  payload: string
}

export const RUN_DETAIL_TITLE = 'Urgent issue → Slack'
export const RUN_DETAIL_TOTAL = '0.4s'

export const RUN_STEPS: RunStep[] = [
  {
    icon: 'GH', iconBg: '#24292f', slug: 'github',
    title: 'Trigger received', ms: '12ms',
    payload: `{
  "event": "issues.labeled",
  "label": "urgent",
  "issue": 4821,
  "repo": "runmycrew/api"
}`,
  },
  {
    icon: 'IF', iconBg: '#3a3f4a',
    title: 'Condition passed', ms: '3ms',
    payload: `{
  "assignee": null,
  "matched": true
}`,
  },
  {
    icon: 'SL', iconBg: '#4a154b', slug: 'slack',
    title: 'Slack message sent', ms: '287ms',
    payload: `{
  "channel": "#incidents",
  "ts": "1718...",
  "ok": true
}`,
  },
  {
    icon: 'LN', iconBg: '#5e6ad2', slug: 'linear',
    title: 'Linear issue created', ms: '141ms',
    payload: `{
  "id": "ENG-2703",
  "team": "Platform",
  "priority": 1
}`,
  },
]

/* ─── CHANGELOG ────────────────────────────────────────────────────── */

export const CHANGELOG = [
  { dot: 'var(--primary)', title: 'Crew AI multi-step',  body: 'Generate entire branching workflows from a single sentence.', date: 'JUN 10, 2026' },
  { dot: '#8b5cf6',        title: 'Run replay',          body: 'Re-run any execution with the original payload in one click.', date: 'JUN 3, 2026' },
  { dot: 'var(--chart-2)', title: 'Stripe integration',  body: 'Trigger on charges, refunds and disputes out of the box.',     date: 'MAY 27, 2026' },
  { dot: 'var(--chart-4)', title: 'Team workspaces',     body: 'Share connections and automations across your whole team.',    date: 'MAY 21, 2026' },
] as const

/* ─── TESTIMONIALS ─────────────────────────────────────────────────── */

export const TESTIMONIALS = [
  {
    quote:
      '"RunMyCrew replaced a tangle of scripts and three different tools. Now the whole team just writes what they want and it works."',
    author: 'Bibek Timilsina',
    role: 'Founder, RunMyCrew',
    initial: 'B',
    bg: 'linear-gradient(160deg,#e7e8ff,#d6d9f5)',
    fg: '#1a1b2e',
    avatarBg: '#1a1b2e',
    avatarFg: '#fff',
    subFg: '#54566e',
  },
  {
    quote:
      '"We ship integrations in an afternoon that used to take a sprint. RunMyCrew is the most action-biased tool we run."',
    author: 'Aarav Sharma',
    role: 'Head of Ops, Northwind',
    initial: 'A',
    bg: '#d6f24a',
    fg: '#1a2008',
    avatarBg: '#1a2008',
    avatarFg: '#d6f24a',
    subFg: '#3d4a1a',
  },
] as const

/* ─── FOOTER ───────────────────────────────────────────────────────── */

export type FooterLink = { label: string; href: string }
export type FooterColumn = { title: string; items: FooterLink[] }

export const FOOTER_COLS: FooterColumn[] = [
  {
    title: 'Product',
    items: [
      { label: 'Pricing',      href: '/pricing' },
      { label: 'Integrations', href: '/integrations' },
      { label: 'Templates',    href: '/templates' },
      { label: 'Changelog',    href: '/changelog' },
    ],
  },
  {
    title: 'Developers',
    items: [
      { label: 'Docs',           href: '/docs' },
      { label: 'OAuth scopes',   href: '/oauth-scopes' },
      { label: 'Self-hosting',   href: '/docs/self-host' },
      { label: 'Status',         href: 'https://status.runmycrew.com' },
    ],
  },
  {
    title: 'Company',
    items: [
      { label: 'About',     href: '/about' },
      { label: 'Blog',      href: '/blog' },
      { label: 'Contact',   href: '/contact' },
      { label: 'Security',  href: '/security' },
    ],
  },
  {
    title: 'Legal',
    items: [
      { label: 'Privacy',        href: '/privacy' },
      { label: 'Terms',          href: '/terms' },
      { label: 'Cookies',        href: '/cookies' },
      { label: 'Transparency',   href: '/transparency' },
      { label: 'Data deletion',  href: '/data-deletion' },
    ],
  },
]

export const FOOTER_LEGAL: FooterLink[] = [
  { label: 'Privacy',        href: '/privacy' },
  { label: 'Terms',          href: '/terms' },
  { label: 'Cookies',        href: '/cookies' },
  { label: 'Data deletion',  href: '/data-deletion' },
]
