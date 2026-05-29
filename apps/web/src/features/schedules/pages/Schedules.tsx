import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { useSchedules } from '../hooks/useSchedules'
import { ScheduleList } from '../components/ScheduleList'
import { APP_ROUTES } from '@/shared/constants/routes'

const STATUS_FILTERS = [
  { id: 'all',    label: 'All' },
  { id: 'active', label: 'Active' },
  { id: 'paused', label: 'Paused' },
  { id: 'error',  label: 'Errors' },
]

export function Schedules() {
  const navigate = useNavigate()
  const { data: items = [], isLoading } = useSchedules()

  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  // Detect majority timezone for eyebrow
  const dominantTz = useMemo(() => {
    const tzCounts: Record<string, number> = {}
    items.forEach(s => {
      const tz = s.timezone ?? 'UTC'
      tzCounts[tz] = (tzCounts[tz] ?? 0) + 1
    })
    return Object.entries(tzCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'UTC'
  }, [items])

  const filtered = useMemo(() => {
    let list = items
    if (filter !== 'all') list = list.filter(s => s.status === filter)
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(s =>
        s.name.toLowerCase().includes(q) ||
        (s.cron_expression ?? '').includes(q)
      )
    }
    return list
  }, [items, filter, search])

  const count = (id: string) =>
    id === 'all' ? items.length : items.filter(s => s.status === id).length

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">
            <span className="dot" />
            {items.length} schedule{items.length !== 1 ? 's' : ''} · timezone {dominantTz}
          </span>
          <h1>Schedules</h1>
        </div>
        <div className="btn-group">
          <button
            className="btn btn-secondary"
            onClick={() => navigate(APP_ROUTES.AUTOMATIONS)}
            title="Create a new workflow with a cron trigger in the canvas"
          >
            <Icons.Plus /> New schedule
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="filter-bar">
        <div className="filter-tabs">
          {STATUS_FILTERS.map(f => (
            count(f.id) > 0 || f.id === 'all' ? (
              <button
                key={f.id}
                className={`filter-tab${filter === f.id ? ' active' : ''}`}
                onClick={() => setFilter(f.id)}
              >
                {f.label}
                <span className="filter-count">{count(f.id)}</span>
              </button>
            ) : null
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input
              placeholder="Search by name or cron"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            {search && (
              <button onClick={() => setSearch('')} className="text-[var(--text-faint)] hover:text-[var(--text)] text-[12px]">✕</button>
            )}
          </div>
        </div>
      </div>

      {/* Schedule list */}
      {isLoading ? (
        <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
          <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
          Loading schedules…
        </div>
      ) : (
        <ScheduleList items={filtered} />
      )}
    </div>
  )
}
