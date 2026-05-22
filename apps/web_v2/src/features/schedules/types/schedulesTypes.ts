export type ScheduleState = 'active' | 'error' | 'paused'

export interface Schedule {
  id: number
  name: string
  cron: string
  next: string
  last: string
  state: ScheduleState
}
