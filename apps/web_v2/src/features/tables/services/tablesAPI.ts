import type { DataTable } from '../types/tablesTypes'

const MOCK_TABLES: DataTable[] = [
  { id: 1, name: 'leads',           rows: '4,821',  cols: 12, source: 'HubSpot sync',     updated: '2m ago',  owner: 'Mahesh' },
  { id: 2, name: 'customers',       rows: '12,340', cols: 18, source: 'Stripe + HubSpot',  updated: '1h ago',  owner: 'Priya'  },
  { id: 3, name: 'invoices',        rows: '2,109',  cols: 9,  source: 'Stripe webhook',   updated: '2h ago',  owner: 'Mahesh' },
  { id: 4, name: 'churn_signals',   rows: '891',    cols: 7,  source: 'Agent output',     updated: '6h ago',  owner: 'Priya'  },
  { id: 5, name: 'support_tickets', rows: '3,482',  cols: 14, source: 'Zendesk sync',     updated: '3h ago',  owner: 'Devon'  },
  { id: 6, name: 'product_events',  rows: '98,201', cols: 6,  source: 'Segment webhook',  updated: '30s ago', owner: 'Mahesh' },
  { id: 7, name: 'rfp_inbox',       rows: '134',    cols: 8,  source: 'Gmail + agent',    updated: '1d ago',  owner: 'Mahesh' },
  { id: 8, name: 'pager_rotations', rows: '48',     cols: 5,  source: 'PagerDuty sync',   updated: '4h ago',  owner: 'Devon'  },
]

export const tablesAPI = {
  getAll: async (): Promise<DataTable[]> => MOCK_TABLES,
}
