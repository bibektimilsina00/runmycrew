import type { Automation } from '../types/automationsTypes'

export const MOCK_AUTOMATIONS: Automation[] = [
  { id: 1, name: 'Stripe refund — Slack approval', kind: 'flow', status: 'active', runs: '1,284', last: '2m ago', owner: 'Mahesh' },
  { id: 2, name: 'Lead enrichment — Clearbit → HubSpot', kind: 'flow', status: 'active', runs: '812', last: '4m ago', owner: 'Mahesh' },
  { id: 3, name: 'Daily brief from Linear + GitHub', kind: 'agent', status: 'active', runs: '302', last: '1h ago', owner: 'Priya' },
  { id: 4, name: 'Inbound RFP classifier', kind: 'agent', status: 'active', runs: '489', last: 'now', owner: 'Mahesh' },
  { id: 5, name: 'Notion → Airtable nightly sync', kind: 'schedule', status: 'error', runs: '67', last: '2h ago', owner: 'Priya' },
  { id: 6, name: 'Invoice triage agent', kind: 'agent', status: 'active', runs: '201', last: '3h ago', owner: 'Mahesh' },
  { id: 7, name: 'Support ticket auto-tagger', kind: 'agent', status: 'active', runs: '1,012', last: '4h ago', owner: 'Devon' },
  { id: 8, name: 'Weekly metrics digest', kind: 'schedule', status: 'active', runs: '52', last: '5h ago', owner: 'Priya' },
  { id: 9, name: 'Pager rotation handoff', kind: 'flow', status: 'paused', runs: '146', last: '1d ago', owner: 'Devon' },
  { id: 10, name: 'Churn-risk watchlist', kind: 'agent', status: 'active', runs: '97', last: '1d ago', owner: 'Priya' },
  { id: 11, name: 'Contract redline assistant', kind: 'agent', status: 'draft', runs: '—', last: '—', owner: 'Mahesh' },
]

export const automationsAPI = {
  getAll: async (): Promise<Automation[]> => MOCK_AUTOMATIONS,
}
