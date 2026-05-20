import React, { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, Play, Clock, Zap, Globe, MoreHorizontal, Pencil, Trash2, ToggleLeft, ToggleRight, Copy } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { requestJson } from '@/lib/api/client'
import { useCreateWorkflow, useDeleteWorkflow, useUpdateWorkflow, useDuplicateWorkflow } from '@/features/dashboard/hooks/use-workflows'
import { cn } from '@/lib/utils'

const WorkflowWithStatsSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  color: z.string().nullable().optional(),
  is_active: z.boolean().optional(),
  trigger_type: z.string().optional(),
  execution_count: z.number().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})
type WorkflowWithStats = z.infer<typeof WorkflowWithStatsSchema>

function useWorkflowsWithStats() {
  return useQuery({
    queryKey: ['workflows', 'with-stats'],
    queryFn: () => requestJson(z.array(WorkflowWithStatsSchema), { url: '/workflows/with-stats', method: 'GET' }),
    staleTime: 30_000,
  })
}

const TRIGGER_ICON: Record<string, React.FC<any>> = {
  webhook: Globe,
  cron: Clock,
  manual: Play,
}

const STATUS_COLORS: Record<string, string> = {
  running: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  paused: 'bg-yellow-500',
}

function WorkflowCard({ wf, onOpen, onDelete, onToggle, onDuplicate }: {
  wf: WorkflowWithStats
  onOpen: () => void
  onDelete: () => void
  onToggle: () => void
  onDuplicate: () => void
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  const TriggerIcon = TRIGGER_ICON[wf.trigger_type || 'manual'] ?? Play
  const color = wf.color || '#6366f1'
  const isActive = wf.is_active !== false

  return (
    <div
      onClick={onOpen}
      className="group relative flex flex-col p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] hover:border-[var(--border-focus)] cursor-pointer transition-all"
    >
      {/* Color bar */}
      <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-xl" style={{ backgroundColor: color }} />

      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${color}22` }}>
            <TriggerIcon className="w-4 h-4" style={{ color }} />
          </div>
          <div className="min-w-0">
            <p className="text-[13px] font-semibold text-white truncate">{wf.name}</p>
            {wf.description && <p className="text-[11px] text-[var(--text-muted)] truncate">{wf.description}</p>}
          </div>
        </div>

        <div className="relative flex-shrink-0" onClick={e => e.stopPropagation()}>
          <button
            onClick={() => setMenuOpen(v => !v)}
            className="p-1 rounded hover:bg-[var(--bg-surface-2)] text-[var(--text-muted)] hover:text-white transition-colors opacity-0 group-hover:opacity-100"
          >
            <MoreHorizontal className="w-4 h-4" />
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-7 z-20 w-40 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg shadow-xl overflow-hidden" onMouseLeave={() => setMenuOpen(false)}>
              <button onClick={onOpen} className="flex items-center gap-2 w-full px-3 py-2 text-[12px] text-white hover:bg-[var(--bg-surface-2)] transition-colors">
                <Pencil className="w-3.5 h-3.5" /> Open
              </button>
              <button onClick={() => { onDuplicate(); setMenuOpen(false) }} className="flex items-center gap-2 w-full px-3 py-2 text-[12px] text-white hover:bg-[var(--bg-surface-2)] transition-colors">
                <Copy className="w-3.5 h-3.5" /> Duplicate
              </button>
              <button onClick={() => { onToggle(); setMenuOpen(false) }} className="flex items-center gap-2 w-full px-3 py-2 text-[12px] text-white hover:bg-[var(--bg-surface-2)] transition-colors">
                {isActive ? <ToggleRight className="w-3.5 h-3.5 text-green-400" /> : <ToggleLeft className="w-3.5 h-3.5 text-[var(--text-muted)]" />}
                {isActive ? 'Deactivate' : 'Activate'}
              </button>
              <button onClick={() => { onDelete(); setMenuOpen(false) }} className="flex items-center gap-2 w-full px-3 py-2 text-[12px] text-red-400 hover:bg-[var(--bg-surface-2)] transition-colors">
                <Trash2 className="w-3.5 h-3.5" /> Delete
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between mt-auto pt-3 border-t border-[var(--border-default)]">
        <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
          <span className="flex items-center gap-1">
            <Zap className="w-3 h-3" />
            {wf.execution_count ?? 0} runs
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className={cn('w-1.5 h-1.5 rounded-full', isActive ? 'bg-green-400' : 'bg-[var(--text-muted)]')} />
          <span className="text-[11px] text-[var(--text-muted)]">{isActive ? 'Active' : 'Inactive'}</span>
        </div>
      </div>
    </div>
  )
}

export const WorkflowsPage: React.FC = () => {
  const navigate = useNavigate()
  const { data: workflows = [], isLoading, refetch } = useWorkflowsWithStats()
  const createWorkflow = useCreateWorkflow()
  const deleteWorkflow = useDeleteWorkflow()
  const updateWorkflow = useUpdateWorkflow()
  const duplicateWorkflow = useDuplicateWorkflow()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive'>('all')

  const filtered = useMemo(() => {
    return workflows.filter(wf => {
      const matchesSearch = !search || wf.name.toLowerCase().includes(search.toLowerCase())
      const matchesFilter = filter === 'all' || (filter === 'active' ? wf.is_active !== false : wf.is_active === false)
      return matchesSearch && matchesFilter
    })
  }, [workflows, search, filter])

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this workflow? This cannot be undone.')) return
    await deleteWorkflow.mutateAsync(id)
    refetch()
  }

  const handleToggle = async (wf: WorkflowWithStats) => {
    await updateWorkflow.mutateAsync({ id: wf.id, is_active: !wf.is_active, silent: true })
    refetch()
  }

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[20px] font-bold text-white">Workflows</h1>
            <p className="text-[13px] text-[var(--text-muted)] mt-0.5">{workflows.length} total</p>
          </div>
          <button
            onClick={() => createWorkflow.mutate()}
            className="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-[13px] font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" /> New Workflow
          </button>
        </div>

        {/* Search + Filter */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search workflows..."
              className="w-full pl-9 pr-4 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg text-[13px] text-white placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border-focus)]"
            />
          </div>
          <div className="flex rounded-lg border border-[var(--border-default)] overflow-hidden">
            {(['all', 'active', 'inactive'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  'px-3 py-2 text-[12px] font-medium capitalize transition-colors',
                  filter === f ? 'bg-indigo-600 text-white' : 'text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-surface-2)]'
                )}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-32 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-default)] animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-24">
            <p className="text-[14px] text-[var(--text-muted)]">{search ? 'No workflows match your search' : 'No workflows yet'}</p>
            {!search && (
              <button onClick={() => createWorkflow.mutate()} className="mt-3 text-[13px] text-indigo-400 hover:text-indigo-300 transition-colors">
                Create your first workflow →
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filtered.map(wf => (
              <WorkflowCard
                key={wf.id}
                wf={wf}
                onOpen={() => navigate(`/workflows/${wf.id}`)}
                onDelete={() => handleDelete(wf.id)}
                onToggle={() => handleToggle(wf)}
                onDuplicate={() => duplicateWorkflow.mutate(wf.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
