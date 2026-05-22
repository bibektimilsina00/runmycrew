import type { KnowledgeSource } from '../types/knowledgeTypes'

const MOCK_KNOWLEDGE: KnowledgeSource[] = [
  { id: 1, name: 'Stripe refund policy',          kind: 'doc',    items: 1,   tokens: '2.4k',  used: 24, updated: '3d ago', state: 'indexed' },
  { id: 2, name: 'Customer escalation playbook',  kind: 'doc',    items: 1,   tokens: '8.1k',  used: 81, updated: '1w ago', state: 'indexed' },
  { id: 3, name: 'Engineering oncall runbook',    kind: 'notion', items: 12,  tokens: '12.3k', used: 62, updated: '2d ago', state: 'indexed' },
  { id: 4, name: 'Pricing FAQ',                   kind: 'site',   items: 8,   tokens: '3.8k',  used: 38, updated: '5d ago', state: 'stale'   },
  { id: 5, name: 'Lead scoring rubric',           kind: 'doc',    items: 1,   tokens: '5.2k',  used: 52, updated: '1d ago', state: 'indexed' },
  { id: 6, name: 'RFP response templates',        kind: 'linear', items: 24,  tokens: '18.7k', used: 90, updated: '4h ago', state: 'syncing' },
  { id: 7, name: '#eng-general Slack archive',    kind: 'slack',  items: 480, tokens: '94.2k', used: 45, updated: '1h ago', state: 'indexed' },
  { id: 8, name: 'Product changelog Q2',          kind: 'csv',    items: 3,   tokens: '4.1k',  used: 10, updated: '1d ago', state: 'indexed' },
]

export const knowledgeAPI = {
  getAll: async (): Promise<KnowledgeSource[]> => MOCK_KNOWLEDGE,
}
