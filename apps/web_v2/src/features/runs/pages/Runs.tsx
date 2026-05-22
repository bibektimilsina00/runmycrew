import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useRuns } from '../hooks/useRuns'
import { RunsTable } from '../components/RunsTable'
import type { RunStatus } from '../types/runsTypes'
import { useToast } from '@/shared/components'

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
  const { toast } = useToast()

  const filtered = filter === 'all' ? items : items.filter(r => r.status === (filter as RunStatus))
  const count = (id: string) => id === 'all' ? items.length : items.filter(r => r.status === id).length

  const handleExport = () => {
    if (filtered.length === 0) {
      toast('No runs to export', { variant: 'warn' })
      return
    }

    const headers = ['ID', 'Status', 'Name', 'Trigger', 'Started', 'Duration']
    const rows = filtered.map((r) => [
      r.id,
      r.status.toUpperCase(),
      `"${r.name.replace(/"/g, '""')}"`,
      `"${r.trigger.replace(/"/g, '""')}"`,
      r.started,
      r.duration,
    ])

    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.setAttribute('href', url)
    link.setAttribute('download', `runs-export-${new Date().toISOString().slice(0, 10)}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    toast('Runs exported successfully', { variant: 'ok' })
  }

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow"><span className="dot animate-pulse" />Live · streaming</span>
          <h1>Runs</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary" onClick={handleExport}><Icons.Download /> Export</button>
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
