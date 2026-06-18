/**
 * Pricing source of truth. Used by both the tier cards and the
 * comparison matrix below them. Update one place; both update.
 */

export type Tier = {
  slug: 'free' | 'pro' | 'enterprise'
  name: string
  price: string          // display string, e.g. '$0' or '$29 / user'
  cadence?: string       // e.g. '/ month'
  tagline: string
  ctaLabel: string
  ctaHref: string
  features: string[]
  highlight?: boolean    // visually featured tier (Pro)
}

export const TIERS: Tier[] = [
  {
    slug: 'free',
    name: 'Free',
    price: '$0',
    cadence: '/ month',
    tagline: 'For solo builders trying Fuse on side projects.',
    ctaLabel: 'Start for free',
    ctaHref: 'https://app.fuse.bibektimilsina.tech/register',
    features: [
      '1 workspace · 1 user',
      '500 workflow runs / month',
      'Up to 5 active workflows',
      '7 days run history',
      'Community support',
    ],
  },
  {
    slug: 'pro',
    name: 'Pro',
    price: '$29',
    cadence: '/ user / month',
    tagline: 'For teams shipping workflows that customers depend on.',
    ctaLabel: 'Start free trial',
    ctaHref: 'https://app.fuse.bibektimilsina.tech/register',
    highlight: true,
    features: [
      'Unlimited workspaces',
      '50,000 runs / month included',
      'Unlimited active workflows',
      '30 days run history',
      'Run replay + alerts',
      'Email support, 1 business day SLA',
    ],
  },
  {
    slug: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    tagline: 'For organisations with compliance, SSO and region pinning.',
    ctaLabel: 'Talk to sales',
    ctaHref: '/contact',
    features: [
      'Everything in Pro',
      'SSO (SAML) + SCIM',
      'Audit log export',
      'Region pinning + private VPC',
      'Custom rate limits',
      'Dedicated support + 99.95% SLA',
    ],
  },
]

export type ComparisonGroup = {
  group: string
  rows: { label: string; free: string | boolean; pro: string | boolean; enterprise: string | boolean }[]
}

export const COMPARISON: ComparisonGroup[] = [
  {
    group: 'Usage',
    rows: [
      { label: 'Workflow runs / month',     free: '500',         pro: '50,000',       enterprise: 'Custom' },
      { label: 'Active workflows',          free: '5',           pro: 'Unlimited',    enterprise: 'Unlimited' },
      { label: 'Run history retention',     free: '7 days',      pro: '30 days',      enterprise: 'Up to 1 year' },
      { label: 'Workspaces',                free: '1',           pro: 'Unlimited',    enterprise: 'Unlimited' },
      { label: 'Seats',                     free: '1',           pro: 'Per user',     enterprise: 'Per user' },
    ],
  },
  {
    group: 'Build',
    rows: [
      { label: 'Fuse AI prompt → workflow', free: true,  pro: true,  enterprise: true  },
      { label: 'OAuth integrations',         free: true,  pro: true,  enterprise: true  },
      { label: 'Webhook + schedule triggers', free: true, pro: true,  enterprise: true  },
      { label: 'Custom apps (HTTP nodes)',   free: false, pro: true,  enterprise: true  },
      { label: 'Conditional branching',      free: true,  pro: true,  enterprise: true  },
    ],
  },
  {
    group: 'Observe',
    rows: [
      { label: 'Run logs + payloads',        free: true,  pro: true,  enterprise: true  },
      { label: 'Run replay',                 free: false, pro: true,  enterprise: true  },
      { label: 'Alerts (Slack / email)',     free: false, pro: true,  enterprise: true  },
      { label: 'Audit log export',           free: false, pro: false, enterprise: true  },
    ],
  },
  {
    group: 'Security',
    rows: [
      { label: 'SSO (SAML)',                 free: false, pro: false, enterprise: true  },
      { label: 'SCIM provisioning',          free: false, pro: false, enterprise: true  },
      { label: 'Region pinning',             free: false, pro: false, enterprise: true  },
      { label: 'Private VPC',                free: false, pro: false, enterprise: true  },
      { label: 'Custom DPA',                 free: false, pro: false, enterprise: true  },
    ],
  },
  {
    group: 'Support',
    rows: [
      { label: 'Community Discord',          free: true,  pro: true,  enterprise: true  },
      { label: 'Email support',              free: false, pro: 'Next business day', enterprise: 'Same day' },
      { label: 'Dedicated Slack channel',    free: false, pro: false, enterprise: true  },
      { label: 'Uptime SLA',                 free: false, pro: '99.9%', enterprise: '99.95%' },
    ],
  },
]
