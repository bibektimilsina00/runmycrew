export type ConnectionState = 'ok' | 'warn' | 'err'

export interface Connection {
  id: string
  name: string
  sub: string
  state: ConnectionState
  endpoints: number
  last: string
}
