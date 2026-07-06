import { useState, useMemo } from 'react'
import { Icons } from '@/shared/components/icons'
import { useLoops, useCreateLoop } from '../hooks/useLoops'
import { LoopList } from '../components/LoopList'
import type { LoopKind } from '../types/loopsTypes'

type FilterId = 'all' | LoopKind | 'paused'

const FILTERS: { id: FilterId; label: string }[] = [
  { id: 'all',      label: 'All' },
  { id: 'flow',     label: 'Flows' },
  { id: 'agent',    label: 'Agents' },
  { id: 'schedule', label: 'Scheduled' },
  { id: 'paused',   label: 'Paused' },
]

type SortKey = 'name' | 'runs' | 'last_run' | 'status'
const SORT_OPTIONS: { id: SortKey; label: string }[] = [
  { id: 'name',     label: 'Name' },
  { id: 'runs',     label: 'Most runs' },
  { id: 'last_run', label: 'Recently run' },
  { id: 'status',   label: 'Status' },
]

export function Loops() {
  const { data: items = [], isLoading } = useLoops()
  const createLoop = useCreateLoop()

  const [filter, setFilter]     = useState<FilterId>('all')
  const [search, setSearch]     = useState('')
  const [sortKey, setSortKey]   = useState<SortKey>('last_run')
  const [sortAsc, setSortAsc]   = useState(false)
  const [showSort, setShowSort] = useState(false)

  const filtered = useMemo(() => {
    let list = items

    // kind / status filter
    if (filter === 'paused') list = list.filter(a => a.status === 'paused')
    else if (filter !== 'all') list = list.filter(a => a.kind === filter)

    // search
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(a =>
        a.name.toLowerCase().includes(q) ||
        a.trigger.toLowerCase().includes(q) ||
        a.kind.includes(q)
      )
    }

    // sort
    list = [...list].sort((a, b) => {
      let cmp = 0
      if (sortKey === 'name')     cmp = a.name.localeCompare(b.name)
      if (sortKey === 'runs')     cmp = a.execution_count - b.execution_count
      if (sortKey === 'last_run') cmp = (a.last_run ?? '').localeCompare(b.last_run ?? '')
      if (sortKey === 'status')   cmp = a.status.localeCompare(b.status)
      return sortAsc ? cmp : -cmp
    })

    return list
  }, [items, filter, search, sortKey, sortAsc])

  const count = (id: FilterId) => {
    if (id === 'all')    return items.length
    if (id === 'paused') return items.filter(a => a.status === 'paused').length
    return items.filter(a => a.kind === id).length
  }

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · {items.length} total</span>
          <h1>Crews</h1>
          <p className="text-[13px] text-[var(--text-mute)] mt-[4px]">
            Teams of AI agents that plan, build, and verify their own work in a loop.
          </p>
        </div>
        <div className="btn-group">
          <button
            className="btn btn-primary"
            onClick={() => createLoop.mutate({ name: 'Untitled Loop' })}
            disabled={createLoop.isPending}
          >
            <Icons.Plus /> New loop
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="filter-bar">
        <div className="filter-tabs">
          {FILTERS.map(f => (
            <button
              key={f.id}
              className={`filter-tab${filter === f.id ? ' active' : ''}`}
              onClick={() => setFilter(f.id)}
            >
              {f.label} <span className="filter-count">{count(f.id)}</span>
            </button>
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input
              placeholder="Search by name or trigger"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            {search && <button onClick={() => setSearch('')} className="text-[var(--text-faint)] hover:text-[var(--text)] text-[12px]">✕</button>}
          </div>

          {/* Sort dropdown */}
          <div className="relative">
            <button
              className={`icon-btn${showSort ? ' bg-[var(--surface)]' : ''}`}
              title="Sort"
              onClick={() => setShowSort(v => !v)}
            >
              <Icons.Sort />
            </button>
            {showSort && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowSort(false)} />
                <div className="absolute right-0 top-[calc(100%+6px)] z-50 w-[180px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[11px] p-[5px] shadow-[0_16px_40px_-12px_oklch(0_0_0/0.6)]">
                  {SORT_OPTIONS.map(s => (
                    <button
                      key={s.id}
                      onClick={() => {
                        if (sortKey === s.id) setSortAsc(v => !v)
                        else { setSortKey(s.id); setSortAsc(false) }
                        setShowSort(false)
                      }}
                      className={`flex items-center justify-between w-full px-3 py-2 rounded-[7px] text-[12.5px] font-medium transition-colors hover:bg-[var(--surface)] ${sortKey === s.id ? 'text-[var(--text)]' : 'text-[var(--text-mute)]'}`}
                    >
                      {s.label}
                      {sortKey === s.id && (
                        <span className="text-[10px] text-[var(--text-faint)]">{sortAsc ? '↑' : '↓'}</span>
                      )}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* List */}
      {isLoading ? (
        <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
          <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
          Loading loops…
        </div>
      ) : (
        <LoopList items={filtered} />
      )}
    </div>
  )
}
