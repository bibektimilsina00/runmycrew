/**
 * Curated workflow templates. Each entry shows a 3-step preview chain
 * built from the integration palette so the cards stay visually rich
 * without per-template artwork.
 */

export type TemplateCategory =
  | 'Sales'
  | 'Marketing'
  | 'Engineering'
  | 'Operations'
  | 'Support'
  | 'Internal'

export type TemplateStep = {
  letter: string
  color: string
  label: string
}

export type Template = {
  slug: string
  title: string
  category: TemplateCategory
  description: string
  steps: TemplateStep[]
}

export const TEMPLATE_CATEGORIES: TemplateCategory[] = [
  'Sales',
  'Marketing',
  'Engineering',
  'Operations',
  'Support',
  'Internal',
]

export const TEMPLATES: Template[] = [
  {
    slug: 'urgent-issue-to-slack',
    title: 'Urgent GitHub issue → Slack + Linear',
    category: 'Engineering',
    description: 'Route any GitHub issue labeled "urgent" to #incidents and create a P1 Linear ticket.',
    steps: [
      { letter: 'GH', color: '#24292f', label: 'GitHub trigger' },
      { letter: 'SL', color: '#4a154b', label: 'Slack post' },
      { letter: 'LN', color: '#5e6ad2', label: 'Linear create' },
    ],
  },
  {
    slug: 'meta-lead-to-crm',
    title: 'Meta lead form → Notion CRM',
    category: 'Marketing',
    description: 'When a Meta lead form is submitted, add the lead to Notion and send a welcome email.',
    steps: [
      { letter: 'MT', color: '#0866ff', label: 'Meta lead' },
      { letter: 'NO', color: '#111',    label: 'Notion row' },
      { letter: 'GM', color: '#ea4335', label: 'Gmail send' },
    ],
  },
  {
    slug: 'daily-standup-digest',
    title: 'Daily standup digest',
    category: 'Operations',
    description: 'Every weekday at 9am, summarize new GitHub activity with AI and post it to #standup.',
    steps: [
      { letter: '⏱',  color: '#3a3f4a', label: 'Schedule' },
      { letter: 'GH', color: '#24292f', label: 'GitHub fetch' },
      { letter: 'AI', color: '#5e6ad2', label: 'Claude summarize' },
    ],
  },
  {
    slug: 'stripe-refund-alert',
    title: 'Stripe refund alert',
    category: 'Support',
    description: 'On any Stripe refund, post a Slack alert with the customer + amount and tag the finance team.',
    steps: [
      { letter: 'ST', color: '#635bff', label: 'Stripe refund' },
      { letter: 'IF', color: '#3a3f4a', label: 'Amount > $100' },
      { letter: 'SL', color: '#4a154b', label: 'Slack alert' },
    ],
  },
  {
    slug: 'inbound-lead-router',
    title: 'Inbound lead router',
    category: 'Sales',
    description: 'Score new leads with AI, post hot leads to Slack and assign them in your CRM automatically.',
    steps: [
      { letter: 'GM', color: '#ea4335', label: 'Gmail trigger' },
      { letter: 'AI', color: '#5e6ad2', label: 'Score lead' },
      { letter: 'NO', color: '#111',    label: 'Notion update' },
    ],
  },
  {
    slug: 'docs-publish-sync',
    title: 'Docs publish sync',
    category: 'Internal',
    description: 'When a Google Doc is updated, regenerate the docs site and notify the writing team.',
    steps: [
      { letter: 'GD', color: '#4285f4', label: 'Doc updated' },
      { letter: 'GH', color: '#24292f', label: 'Trigger build' },
      { letter: 'SL', color: '#4a154b', label: 'Notify team' },
    ],
  },
  {
    slug: 'weekly-metrics-digest',
    title: 'Weekly metrics digest',
    category: 'Operations',
    description: 'Every Monday at 7am, pull this week’s GA4 + Stripe metrics and post a digest to Slack.',
    steps: [
      { letter: '⏱',  color: '#3a3f4a', label: 'Schedule' },
      { letter: 'G4', color: '#e67c2f', label: 'GA4 report' },
      { letter: 'AI', color: '#5e6ad2', label: 'AI summary' },
    ],
  },
  {
    slug: 'support-triage-bot',
    title: 'Support triage bot',
    category: 'Support',
    description: 'Classify incoming emails with AI, file high-priority ones in Linear and acknowledge the customer.',
    steps: [
      { letter: 'GM', color: '#ea4335', label: 'Gmail trigger' },
      { letter: 'AI', color: '#5e6ad2', label: 'Classify' },
      { letter: 'LN', color: '#5e6ad2', label: 'Linear ticket' },
    ],
  },
  {
    slug: 'calendar-to-standup',
    title: 'Calendar → standup notes',
    category: 'Engineering',
    description: 'On every calendar event, generate a meeting brief and drop it in the shared Notion page.',
    steps: [
      { letter: 'CA', color: '#4285f4', label: 'Calendar event' },
      { letter: 'AI', color: '#5e6ad2', label: 'Generate brief' },
      { letter: 'NO', color: '#111',    label: 'Notion append' },
    ],
  },
]
