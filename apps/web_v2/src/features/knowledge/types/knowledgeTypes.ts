export type KnowledgeState = 'indexed' | 'syncing' | 'stale'
export type KnowledgeKind = 'doc' | 'site' | 'linear' | 'notion' | 'csv' | 'slack'

export interface KnowledgeSource {
  id: number
  name: string
  kind: KnowledgeKind
  items: number
  tokens: string
  used: number
  updated: string
  state: KnowledgeState
}
