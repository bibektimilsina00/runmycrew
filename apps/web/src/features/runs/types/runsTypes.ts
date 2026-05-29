export type RunStatus = 'ok' | 'err' | 'warn' | 'run'

export interface Run {
  id: string
  status: RunStatus
  name: string
  trigger: string
  started: string
  duration: string
  startedAt: string
}
