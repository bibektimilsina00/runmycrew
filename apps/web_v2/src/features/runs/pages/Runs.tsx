import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useRuns } from '../hooks/useRuns'
import { RunsTable } from '../components/RunsTable'
import type { RunStatus } from '../types/runsTypes'

const FILTERS: { id: string; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'ok', label: 'Success' },
  { id: 'err', label: 'Failed' },
  { id: 'warn', label: 'Warning' },
  { id: 'run', label: 'Running' },
]

export function Runs() {
  const { items } = useRuns()
  const [filter, setFilter] = useState('all')

  const filtered = filter === 'all' ? items : items.filter(r => r.status === (filter as RunStatus))
  const count = (id: string) => id === 'all' ? items.length : items.filter(r => r.status === id).length

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow"><span className="dot" />Live · streaming</span>
          <h1>Runs</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icons.Download /> Export</button>
          <button className="btn btn-secondary"><Icons.Pause /> Pause stream</button>
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
            <input placeholder="Filter by name or trigger" />
          </div>
          <button className="icon-btn" title="Sort"><Icons.Sort /></button>
        </div>
      </div>

      <RunsTable items={filtered} />
    </div>
  )
}
