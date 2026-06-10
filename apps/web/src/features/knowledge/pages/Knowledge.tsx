import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { useToast, useConfirm } from '@/shared/components'
import { useKBList, useDeleteKB } from '../hooks/useKnowledge'
import { KnowledgeList } from '../components/KnowledgeList'
import { CreateKBModal } from '../components/CreateKBModal'
import { APP_ROUTES } from '@/shared/constants/routes'
import { isKBConfigured, type KnowledgeBase } from '../types/knowledgeTypes'

export function Knowledge() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const confirm = useConfirm()

  const { data: kbs = [], isLoading } = useKBList()
  const deleteKB = useDeleteKB()

  const [search, setSearch]     = useState('')
  const [tab, setTab]           = useState<'all' | 'setup'>('all')
  const [createOpen, setCreateOpen] = useState(false)

  const totalChunks = kbs.reduce((s, kb) => s + kb.total_chunks, 0)
  const fmtChunks = (n: number) => n >= 1_000_000 ? `${(n/1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n/1_000).toFixed(1)}k` : String(n)

  const setupCount = useMemo(() => kbs.filter(k => !isKBConfigured(k)).length, [kbs])

  const filtered = useMemo(() => {
    const byTab = tab === 'setup' ? kbs.filter(k => !isKBConfigured(k)) : kbs
    if (!search.trim()) return byTab
    const q = search.toLowerCase()
    return byTab.filter(kb =>
      kb.name.toLowerCase().includes(q) ||
      (kb.description ?? '').toLowerCase().includes(q)
    )
  }, [kbs, search, tab])

  const handleDelete = async (kb: KnowledgeBase) => {
    const ok = await confirm({
      title: 'Delete knowledge base',
      message: `Delete "${kb.name}"? All ${kb.document_count} documents and ${kb.total_chunks} chunks will be permanently removed.`,
      confirmText: 'Delete', variant: 'danger',
    })
    if (!ok) return
    await deleteKB.mutateAsync(kb.id)
    toast('Knowledge base deleted', { variant: 'ok' })
  }

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Retrieval · {fmtChunks(totalChunks)} chunks indexed</span>
          <h1>Knowledge base</h1>
        </div>
        <button className="btn btn-primary" onClick={() => setCreateOpen(true)}>
          <Icons.Plus /> New knowledge base
        </button>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          <button
            className={`filter-tab ${tab === 'all' ? 'active' : ''}`}
            onClick={() => setTab('all')}
          >
            All <span className="filter-count">{kbs.length}</span>
          </button>
          <button
            className={`filter-tab ${tab === 'setup' ? 'active' : ''}`}
            onClick={() => setTab('setup')}
          >
            Setup required <span className="filter-count">{setupCount}</span>
          </button>
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input placeholder="Search knowledge bases" value={search} onChange={e => setSearch(e.target.value)} />
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
          <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
          Loading…
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          tab={tab}
          searching={!!search.trim()}
          hasAny={kbs.length > 0}
          onCreate={() => setCreateOpen(true)}
          onClearSearch={() => setSearch('')}
        />
      ) : (
        <KnowledgeList items={filtered} onDelete={handleDelete} />
      )}

      {createOpen && (
        <CreateKBModal
          onClose={() => setCreateOpen(false)}
          onCreated={id => {
            setCreateOpen(false)
            navigate(APP_ROUTES.KNOWLEDGE_DETAIL(id))
          }}
        />
      )}
    </div>
  )
}

interface EmptyStateProps {
  tab: 'all' | 'setup'
  searching: boolean
  hasAny: boolean
  onCreate: () => void
  onClearSearch: () => void
}

function EmptyState({ tab, searching, hasAny, onCreate, onClearSearch }: EmptyStateProps) {
  let icon = <Icons.Book style={{ width: 22, height: 22, color: 'var(--text-dim)' }} />
  let title = 'No knowledge bases yet'
  let body  = 'Create one to start indexing documents.'
  let action: { label: string; onClick: () => void; primary?: boolean } | null = {
    label: 'New knowledge base', onClick: onCreate, primary: true,
  }

  if (searching) {
    icon   = <Icons.Search style={{ width: 20, height: 20, color: 'var(--text-dim)' }} />
    title  = 'No matches'
    body   = 'No knowledge bases match your search.'
    action = { label: 'Clear search', onClick: onClearSearch }
  } else if (tab === 'setup') {
    icon   = <Icons.Check style={{ width: 22, height: 22, color: 'var(--text-dim)' }} />
    title  = hasAny ? 'All set' : 'Nothing to set up yet'
    body   = hasAny
      ? 'Every knowledge base is configured.'
      : 'Create one — it runs on the Fuse default model out of the box.'
    action = hasAny
      ? null
      : { label: 'New knowledge base', onClick: onCreate, primary: true }
  }

  return (
    <div className="flex flex-1 items-center justify-center min-h-[50vh]">
      <div className="flex flex-col items-center gap-3 text-center">
        {icon}
        <div className="flex flex-col gap-0.5">
          <span className="text-[13px] text-[var(--text-mute)]">{title}</span>
          <span className="text-[12px] text-[var(--text-faint)]">{body}</span>
        </div>
        {action && (
          <button
            onClick={action.onClick}
            className={action.primary ? 'btn btn-primary mt-1' : 'btn btn-secondary mt-1'}
          >
            {action.primary && <Icons.Plus style={{ width: 13, height: 13 }} />}
            {action.label}
          </button>
        )}
      </div>
    </div>
  )
}
