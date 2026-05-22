import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useVariables } from '../hooks/useVariables'
import { VariablesTable } from '../components/VariablesTable'

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'secrets', label: 'Secrets' },
  { id: 'shared', label: 'Shared' },
  { id: 'production', label: 'Production' },
]

export function Variables() {
  const { items } = useVariables()
  const [filter, setFilter] = useState('all')

  const filtered = filter === 'all' ? items
    : filter === 'secrets' ? items.filter(v => !v.plain)
    : filter === 'shared' ? items.filter(v => v.scope === 'Shared')
    : items.filter(v => v.scope === 'Production')

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · 18 variables · 5 secrets</span>
          <h1>Variables</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icons.Download /> Export</button>
          <button className="btn btn-primary"><Icons.Plus /> New variable</button>
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
            <input placeholder="Search variables" />
          </div>
          <button className="icon-btn" title="Sort"><Icons.Sort /></button>
        </div>
      </div>

      <VariablesTable items={filtered} />
    </div>
  )
}
