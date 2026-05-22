import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useKnowledge } from '../hooks/useKnowledge'
import { KnowledgeList } from '../components/KnowledgeList'

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'doc', label: 'Documents' },
  { id: 'live', label: 'Live sources' },
  { id: 'stale', label: 'Stale' },
]

export function Knowledge() {
  const { items } = useKnowledge()
  const [filter, setFilter] = useState('all')

  const filtered = filter === 'all' ? items
    : filter === 'stale' ? items.filter(k => k.state === 'stale')
    : filter === 'live' ? items.filter(k => k.kind === 'site' || k.kind === 'slack' || k.kind === 'linear')
    : items.filter(k => k.kind === 'doc' || k.kind === 'csv' || k.kind === 'notion')

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Retrieval · 4.2M tokens indexed</span>
          <h1>Knowledge base</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icons.Plus /> Add source</button>
          <button className="btn btn-primary"><Icons.Doc /> Upload document</button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          {FILTERS.map(f => (
            <button key={f.id} className={`filter-tab${filter === f.id ? ' active' : ''}`} onClick={() => setFilter(f.id)}>
              {f.label}
            </button>
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input placeholder="Search knowledge sources" />
          </div>
        </div>
      </div>

      <KnowledgeList items={filtered} />
    </div>
  )
}
