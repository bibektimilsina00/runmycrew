import type { Run } from '../types/runsTypes'

const MOCK_RUNS: Run[] = [
  { id: 1, status: 'ok', name: 'Stripe refund — Slack approval', trigger: 'stripe.charge.refunded', started: '14:42:01', duration: '1.4s' },
  { id: 2, status: 'ok', name: 'Lead enrichment — Clearbit → HubSpot', trigger: 'hubspot.contact.created', started: '14:38:12', duration: '3.1s' },
  { id: 3, status: 'run', name: 'Inbound RFP classifier', trigger: 'imap.inbox.new', started: '14:37:55', duration: 'running…' },
  { id: 4, status: 'ok', name: 'Daily brief from Linear + GitHub', trigger: 'schedule.daily', started: '09:00:00', duration: '8.7s' },
  { id: 5, status: 'err', name: 'Notion → Airtable nightly sync', trigger: 'schedule.0_2_*_*_*', started: '02:00:00', duration: '12.4s' },
  { id: 6, status: 'ok', name: 'Invoice triage agent', trigger: 'gmail.label.invoice', started: '11:14:30', duration: '5.9s' },
  { id: 7, status: 'warn', name: 'Support ticket auto-tagger', trigger: 'zendesk.ticket.new', started: '10:02:18', duration: '2.2s' },
  { id: 8, status: 'ok', name: 'Weekly metrics digest', trigger: 'schedule.weekly', started: '09:00:00', duration: '11.0s' },
  { id: 9, status: 'ok', name: 'Pager rotation handoff', trigger: 'schedule.18h', started: '08:30:00', duration: '0.8s' },
  { id: 10, status: 'ok', name: 'Churn-risk watchlist refresh', trigger: 'schedule.6h', started: '06:00:00', duration: '22.1s' },
  { id: 11, status: 'ok', name: 'Contract redline assistant', trigger: 'gmail.attachment.pdf', started: '05:18:42', duration: '7.3s' },
  { id: 12, status: 'ok', name: 'Support ticket auto-tagger', trigger: 'zendesk.ticket.new', started: '04:55:11', duration: '1.9s' },
]

export const runsAPI = {
  getAll: async (): Promise<Run[]> => MOCK_RUNS,
}
