export type RunStatus = 'ok' | 'run' | 'err' | 'warn'
export type ConnectionState = 'ok' | 'warn' | 'err'

export interface RunItem {
  status: RunStatus
  name: string
  trigger: string
  duration: string
  ago: string
}

export interface ConnectionItem {
  id: string
  name: string
  sub: string
  state: ConnectionState
}

export interface ScheduleItem {
  time: string
  name: string
  sub: string
}

export interface DashboardStats {
  activeWorkflows: number
  runsToday: number
  errorsToday: number
  connectedApps: number
}
