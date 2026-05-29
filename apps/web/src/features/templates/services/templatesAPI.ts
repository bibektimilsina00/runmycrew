import type { Template } from '../types/templatesTypes'

const MOCK_TEMPLATES: Template[] = [
  { idx: '01', label: 'Revenue ops', title: 'Stripe refund — Slack approval', kind: 'flow', steps: 4, bg: 'inspo-bg-1' },
  { idx: '02', label: 'Sales', title: 'Lead enrichment — Clearbit → HubSpot', kind: 'flow', steps: 5, bg: 'inspo-bg-2' },
  { idx: '03', label: 'Engineering', title: 'Daily brief from Linear + GitHub', kind: 'agent', steps: 6, bg: 'inspo-bg-3' },
  { idx: '04', label: 'Inbox', title: 'Inbound RFP classifier', kind: 'agent', steps: 3, bg: 'inspo-bg-1' },
  { idx: '05', label: 'Reporting', title: 'Weekly metrics digest', kind: 'schedule', steps: 7, bg: 'inspo-bg-2' },
  { idx: '06', label: 'Revenue ops', title: 'Churn-risk watchlist alert', kind: 'agent', steps: 5, bg: 'inspo-bg-3' },
]

export const templatesAPI = {
  getAll: async (): Promise<Template[]> => MOCK_TEMPLATES,
}
