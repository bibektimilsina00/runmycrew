import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { Search, ExternalLink, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react'
import { requestJson } from '@/lib/api/client'
import { cn } from '@/lib/utils'

const ExecutionRowSchema = z.object({
  id: z.string(),
  workflow_id: z.string(),
  workflow_name: z.string(),
  workflow_color: z.string().nullable().optional(),
  status: z.string(),
  trigger_type: z.string(),
  started_at: z.string().nullable().optional(),
  finished_at: z.string().nullable().optional(),
  duration_ms: z.number().nullable().optional(),
})

const ExecutionsResponseSchema = z.object({
  executions: z.array(ExecutionRowSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
})

const STATUS_STYLES: Record<string, { dot: string; text: string; label: string }> = {
  completed: { dot: 'bg-green-400', text: 'text-green-400', label: 'Completed' },
  failed:    { dot: 'bg-red-400',   text: 'text-red-400',   label: 'Failed'    },
  running:   { dot: 'bg-blue-400 animate-pulse', text: 'text-blue-400', label: 'Running' },
  paused:    { dot: 'bg-yellow-400', text: 'text-yellow-400', label: 'Paused'  },
  pending:   { dot: 'bg-[var(--text-muted)]', text: 'text-[var(--text-muted)]', label: 'Pending' },
}

const TRIGGER_LABELS: Record<string, string> = {
  manual: 'Manual',
  webhook: 'Webhook',
  cron: 'Schedule',
  'trigger.cron': 'Schedule',
  'trigger.webhook': 'Webhook',
}

function formatDuration(ms: number | null | undefined): string {
  if (!ms) return '—'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60_000) return 'just now'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const PAGE_SIZE = 25

export const ExecutionsPage: React.FC = () => {
  const navigate = useNavigate()
  const [page, setPage] = useState(0)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['executions', 'all', page, statusFilter],
    queryFn: () => requestJson(ExecutionsResponseSchema, {
      url: '/executions/all',
      method: 'GET',
      params: {
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        ...(statusFilter ? { status: statusFilter } : {}),
      },
    }),
    staleTime: 10_000,
  })

  const executions = data?.executions ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const filtered = search
    ? executions.filter(e => e.workflow_name.toLowerCase().includes(search.toLowerCase()))
    : executions

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[20px] font-bold text-white">Executions</h1>
            <p className="text-[13px] text-[var(--text-muted)] mt-0.5">
              {total > 0 ? `${total} total` : 'No executions yet'}
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className={cn('p-2 rounded-lg border border-[var(--border-default)] text-[var(--text-muted)] hover:text-white transition-colors', isFetching && 'opacity-50')}
          >
            <RefreshCw className={cn('w-4 h-4', isFetching && 'animate-spin')} />
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mb-5">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-muted)]" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Filter by workflow..."
              className="w-full pl-9 pr-4 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[13px] text-white placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border-focus)]"
            />
          </div>
          <div className="flex rounded-lg border border-[var(--border-default)] overflow-hidden">
            {[
              { value: '', label: 'All' },
              { value: 'completed', label: 'Completed' },
              { value: 'failed', label: 'Failed' },
              { value: 'running', label: 'Running' },
            ].map(opt => (
              <button
                key={opt.value}
                onClick={() => { setStatusFilter(opt.value); setPage(0) }}
                className={cn(
                  'px-3 py-2 text-[12px] font-medium transition-colors',
                  statusFilter === opt.value ? 'bg-indigo-600 text-white' : 'text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-surface-2)]'
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="rounded-xl border border-[var(--border-default)] overflow-hidden">
          {/* Table head */}
          <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_40px] gap-4 px-4 py-2.5 bg-[var(--bg-surface-2)] border-b border-[var(--border-default)]">
            {['Workflow', 'Status', 'Trigger', 'Duration', 'Started', ''].map(h => (
              <span key={h} className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wide">{h}</span>
            ))}
          </div>

          {isLoading ? (
            <div className="flex flex-col">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-12 border-b border-[var(--border-default)] animate-pulse bg-[var(--bg-surface)]" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 text-[13px] text-[var(--text-muted)]">
              {search ? 'No matching executions' : 'No executions found'}
            </div>
          ) : (
            filtered.map(ex => {
              const s = STATUS_STYLES[ex.status] ?? STATUS_STYLES.pending
              const color = ex.workflow_color || '#6366f1'
              return (
                <div
                  key={ex.id}
                  onClick={() => navigate(`/executions/${ex.id}`)}
                  className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_40px] gap-4 items-center px-4 py-3 border-b border-[var(--border-default)] hover:bg-[var(--bg-surface-2)] transition-colors group cursor-pointer"
                >
                  {/* Workflow */}
                  <button
                    onClick={(e) => { e.stopPropagation(); navigate(`/workflows/${ex.workflow_id}`) }}
                    className="flex items-center gap-2.5 min-w-0 text-left"
                  >
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                    <span className="text-[13px] text-white truncate hover:text-indigo-300 transition-colors">{ex.workflow_name}</span>
                  </button>

                  {/* Status */}
                  <div className="flex items-center gap-1.5">
                    <div className={cn('w-1.5 h-1.5 rounded-full', s.dot)} />
                    <span className={cn('text-[12px] font-medium', s.text)}>{s.label}</span>
                  </div>

                  {/* Trigger */}
                  <span className="text-[12px] text-[var(--text-muted)]">
                    {TRIGGER_LABELS[ex.trigger_type] ?? ex.trigger_type}
                  </span>

                  {/* Duration */}
                  <span className="text-[12px] text-[var(--text-muted)] font-mono">
                    {formatDuration(ex.duration_ms)}
                  </span>

                  {/* Started */}
                  <span className="text-[12px] text-[var(--text-muted)]">
                    {formatTime(ex.started_at)}
                  </span>

                  {/* Open workflow */}
                  <button
                    onClick={(e) => { e.stopPropagation(); navigate(`/workflows/${ex.workflow_id}`) }}
                    className="p-1 rounded text-[var(--text-muted)] hover:text-white opacity-0 group-hover:opacity-100 transition-all"
                    title="Open workflow"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                </div>
              )
            })
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <span className="text-[12px] text-[var(--text-muted)]">
              Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 rounded border border-[var(--border-default)] text-[var(--text-muted)] hover:text-white disabled:opacity-30 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-[12px] text-white">{page + 1} / {totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 rounded border border-[var(--border-default)] text-[var(--text-muted)] hover:text-white disabled:opacity-30 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
