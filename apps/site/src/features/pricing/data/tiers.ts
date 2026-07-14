/**
 * Pricing source of truth. Used by both the tier cards and the
 * comparison matrix below them. Update one place; both update.
 */
import { EXTERNAL_LINKS } from '@/shared/constants/routes'

export type Tier = {
  slug: 'free' | 'pro' | 'enterprise'
  name: string
  price: string          // current display price — 'Free' during early access
  cadence?: string       // e.g. '/ month'
  priceLater?: string    // planned price once paid plans launch (shown muted)
  tagline: string
  ctaLabel: string
  ctaHref: string
  features: string[]
  highlight?: boolean    // visually featured tier (Pro)
}

// Early access: every plan is free right now. `priceLater` keeps the eventual
// price visible so it's honest, not a bait-and-switch — but nobody is charged
// today and no card is required.
export const TIERS: Tier[] = [
  {
    slug: 'free',
    name: 'Free',
    price: 'Free',
    tagline: 'For solo builders. Stays free — forever.',
    ctaLabel: 'Start building',
    ctaHref: EXTERNAL_LINKS.REGISTER,
    features: [
      '1 workspace · 1 user',
      'Generous run limits',
      'All core nodes & integrations',
      'Run history & logs',
      'Community support',
    ],
  },
  {
    slug: 'pro',
    name: 'Pro',
    price: 'Free',
    cadence: 'in early access',
    priceLater: 'later ~$29 / user / mo',
    tagline: 'For teams shipping workflows customers depend on.',
    ctaLabel: 'Start free — no card',
    ctaHref: EXTERNAL_LINKS.REGISTER,
    highlight: true,
    features: [
      'Everything, unlocked while in early access',
      'Unlimited workspaces & workflows',
      'Full run history, replay + alerts',
      'Custom apps (HTTP nodes)',
      'Priority email support',
      'Founder pricing when paid plans launch',
    ],
  },
  {
    slug: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    tagline: 'For orgs needing compliance, SSO and region pinning.',
    ctaLabel: 'Talk to us',
    ctaHref: '/contact',
    features: [
      'Everything in Pro',
      'SSO (SAML) + SCIM',
      'Audit log export',
      'Region pinning + private VPC',
      'Custom rate limits',
      'Dedicated support + SLA',
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
      { label: 'Crew AI prompt → workflow', free: true,  pro: true,  enterprise: true  },
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
