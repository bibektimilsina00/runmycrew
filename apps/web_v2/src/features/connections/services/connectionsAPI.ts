import type { Connection } from '../types/connectionsTypes'

const MOCK_CONNECTIONS: Connection[] = [
  { id: 'stripe',     name: 'Stripe',     sub: 'Payments & billing',      state: 'ok',   endpoints: 12, last: '2m ago' },
  { id: 'slack',      name: 'Slack',      sub: '3 workspaces connected',  state: 'ok',   endpoints: 8,  last: '2m ago' },
  { id: 'linear',     name: 'Linear',     sub: 'fuse-engineering team',   state: 'ok',   endpoints: 6,  last: '1h ago' },
  { id: 'github',     name: 'GitHub',     sub: 'fuse-labs · 4 repos',     state: 'ok',   endpoints: 5,  last: '1h ago' },
  { id: 'hubspot',    name: 'HubSpot',    sub: 'auth failed · re-link',   state: 'err',  endpoints: 9,  last: '2h ago' },
  { id: 'notion',     name: 'Notion',     sub: 'token expires in 4d',     state: 'warn', endpoints: 4,  last: '4h ago' },
  { id: 'clearbit',   name: 'Clearbit',   sub: '892 / 1000 req used',     state: 'warn', endpoints: 3,  last: '4m ago' },
  { id: 'pagerduty',  name: 'PagerDuty',  sub: 'ops-primary team',        state: 'ok',   endpoints: 4,  last: '4h ago' },
  { id: 'zendesk',    name: 'Zendesk',    sub: 'support.fuse.io',         state: 'ok',   endpoints: 7,  last: '3h ago' },
]

export const connectionsAPI = {
  getAll: async (): Promise<Connection[]> => MOCK_CONNECTIONS,
}
