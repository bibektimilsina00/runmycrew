export type LogLevel = 'info' | 'warn' | 'err'

export interface LogEntry {
  id: string
  t: string
  lvl: string
  src: string
  msg: string
}
