import type { Schedule } from '../types/schedulesTypes'

const MOCK_SCHEDULES: Schedule[] = [
  { id: 1, name: 'Daily brief from Linear + GitHub', cron: '0 9 * * *', next: 'Tomorrow 09:00', last: '8.7s · ok', state: 'active' },
  { id: 2, name: 'Notion → Airtable nightly sync', cron: '0 2 * * *', next: 'Tomorrow 02:00', last: '12.4s · err', state: 'error' },
  { id: 3, name: 'Weekly metrics digest', cron: '0 9 * * MON', next: 'Mon 09:00', last: '11.0s · ok', state: 'active' },
  { id: 4, name: 'EOD pager rotation handoff', cron: '0 18 * * FRI', next: 'Fri 18:00', last: '1.2s · ok', state: 'active' },
  { id: 5, name: 'Churn-risk watchlist refresh', cron: '0 6 * * *', next: 'Tomorrow 06:00', last: '22.1s · ok', state: 'active' },
  { id: 6, name: 'Monthly billing reconciliation', cron: '0 0 1 * *', next: 'Jun 01 00:00', last: '—', state: 'paused' },
]

export const schedulesAPI = {
  getAll: async (): Promise<Schedule[]> => MOCK_SCHEDULES,
}
