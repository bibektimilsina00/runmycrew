import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useTables } from '../hooks/useTables'
import { TablesTable } from '../components/TablesTable'

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'live', label: 'Live' },
  { id: 'static', label: 'Static' },
  { id: 'archived', label: 'Archived' },
]

export function Tables() {
  const { items } = useTables()
  const [filter, setFilter] = useState('all')

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Data · 8 tables · 14,872 rows</span>
          <h1>Tables</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icons.Download /> Import CSV</button>
          <button className="btn btn-primary"><Icons.Plus /> New table</button>
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
            <input placeholder="Search tables" />
          </div>
          <button className="icon-btn" title="Sort"><Icons.Sort /></button>
        </div>
      </div>

      <TablesTable items={items} />
    </div>
  )
}
