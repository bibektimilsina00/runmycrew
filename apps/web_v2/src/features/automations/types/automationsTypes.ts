export type WorkflowKind = 'flow' | 'agent' | 'schedule'
export type WorkflowStatus = 'active' | 'error' | 'paused' | 'draft'

export interface Automation {
  id: number
  name: string
  kind: WorkflowKind
  status: WorkflowStatus
  runs: string
  last: string
  owner: string
}
