import type { RunItem, ConnectionItem, ScheduleItem, DashboardStats } from '../types/dashboardTypes'

const MOCK_RUNS: RunItem[] = [
  { status: 'ok', name: 'Stripe refund — Slack approval', trigger: 'stripe.charge.refunded', duration: '1.4s', ago: '2m ago' },
  { status: 'ok', name: 'Lead enrichment — Clearbit → HubSpot', trigger: 'hubspot.contact.created', duration: '3.1s', ago: '4m ago' },
  { status: 'run', name: 'Inbound RFP classifier', trigger: 'imap.inbox.new', duration: 'running', ago: 'now' },
  { status: 'ok', name: 'Daily brief from Linear + GitHub', trigger: 'schedule.daily', duration: '8.7s', ago: '1h ago' },
  { status: 'err', name: 'Notion → Airtable nightly sync', trigger: 'schedule.0_2_*_*_*', duration: '12.4s', ago: '2h ago' },
  { status: 'ok', name: 'Invoice triage agent', trigger: 'gmail.label.invoice', duration: '5.9s', ago: '3h ago' },
  { status: 'warn', name: 'Support ticket auto-tagger', trigger: 'zendesk.ticket.new', duration: '2.2s', ago: '4h ago' },
  { status: 'ok', name: 'Weekly metrics digest', trigger: 'schedule.weekly', duration: '11.0s', ago: '5h ago' },
]

const MOCK_CONNECTIONS: ConnectionItem[] = [
  { id: 'stripe', name: 'Stripe', sub: '12 endpoints · 4 webhooks', state: 'ok' },
  { id: 'slack', name: 'Slack', sub: '3 workspaces', state: 'ok' },
  { id: 'linear', name: 'Linear', sub: 'fuse-engineering', state: 'ok' },
  { id: 'notion', name: 'Notion', sub: 'token expires in 4d', state: 'warn' },
  { id: 'hub', name: 'HubSpot', sub: 'auth failed · re-link', state: 'err' },
]

const MOCK_SCHEDULES: ScheduleItem[] = [
  { time: '14:30', name: 'Weekly metrics digest', sub: 'linear · github · stripe' },
  { time: '16:00', name: 'Churn-risk watchlist refresh', sub: 'agent · 6 sources' },
  { time: '18:00', name: 'EOD pager rotation handoff', sub: 'pagerduty · slack' },
  { time: '02:00', name: 'Notion → Airtable sync', sub: 'scheduled · last failed' },
]

const MOCK_STATS: DashboardStats = {
  activeWorkflows: 47,
  runsToday: 1284,
  errorsToday: 3,
  connectedApps: 18,
}

export const dashboardAPI = {
  getRuns: async (): Promise<RunItem[]> => MOCK_RUNS,
  getConnections: async (): Promise<ConnectionItem[]> => MOCK_CONNECTIONS,
  getSchedules: async (): Promise<ScheduleItem[]> => MOCK_SCHEDULES,
  getStats: async (): Promise<DashboardStats> => MOCK_STATS,
}
