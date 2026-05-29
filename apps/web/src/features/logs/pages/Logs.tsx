import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useLogs } from '../hooks/useLogs'
import { LogStream } from '../components/LogStream'

const FILTERS: { id: string; label: string; level?: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'info', label: 'Info', level: 'info' },
  { id: 'warn', label: 'Warning', level: 'warn' },
  { id: 'err', label: 'Error', level: 'err' },
]

export function Logs() {
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  const activeLevel = FILTERS.find((f) => f.id === filter)?.level
  const { items, isLoading, refetch } = useLogs(activeLevel)

  const filtered = items.filter((l) => {
    if (!search.trim()) return true
    const query = search.toLowerCase()
    return l.msg.toLowerCase().includes(query) || l.src.toLowerCase().includes(query)
  })

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">
            <span className="dot" />
            Execution logs
          </span>
          <h1>Logs</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary" onClick={() => refetch()} disabled={isLoading}>
            <Icons.Activity /> Refresh
          </button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              className={`filter-tab${filter === f.id ? ' active' : ''}`}
              onClick={() => setFilter(f.id)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input
              placeholder="Filter by source or message"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      <LogStream items={filtered} totalCount={items.length} />
    </div>
  )
}
