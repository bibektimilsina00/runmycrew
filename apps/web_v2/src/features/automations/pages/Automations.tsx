import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useAutomations } from '../hooks/useAutomations'
import { AutomationList } from '../components/AutomationList'

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'flow', label: 'Flows' },
  { id: 'agent', label: 'Agents' },
  { id: 'schedule', label: 'Scheduled' },
  { id: 'paused', label: 'Paused' },
]

export function Automations() {
  const { items } = useAutomations()
  const [filter, setFilter] = useState('all')

  const filtered = filter === 'all' ? items
    : filter === 'paused' ? items.filter(a => a.status === 'paused')
    : items.filter(a => a.kind === filter)

  const count = (id: string) => id === 'all' ? items.length
    : id === 'paused' ? items.filter(a => a.status === 'paused').length
    : items.filter(a => a.kind === id).length

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · 47 total</span>
          <h1>Automations</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icons.Doc /> Import</button>
          <button className="btn btn-primary"><Icons.Plus /> New automation</button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          {FILTERS.map(f => (
            <button key={f.id} className={`filter-tab${filter === f.id ? ' active' : ''}`} onClick={() => setFilter(f.id)}>
              {f.label} <span className="filter-count">{count(f.id)}</span>
            </button>
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input placeholder="Filter by name, trigger, or owner" />
          </div>
          <button className="icon-btn" title="Sort"><Icons.Sort /></button>
        </div>
      </div>

      <AutomationList items={filtered} />
    </div>
  )
}
