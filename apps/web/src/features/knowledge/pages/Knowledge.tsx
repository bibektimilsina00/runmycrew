import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { useToast, useConfirm } from '@/shared/components'
import { useKBList, useDeleteKB } from '../hooks/useKnowledge'
import { KnowledgeList } from '../components/KnowledgeList'
import { CreateKBModal } from '../components/CreateKBModal'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { KnowledgeBase } from '../types/knowledgeTypes'

export function Knowledge() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const confirm = useConfirm()

  const { data: kbs = [], isLoading } = useKBList()
  const deleteKB = useDeleteKB()

  const [search, setSearch]     = useState('')
  const [createOpen, setCreateOpen] = useState(false)

  const totalChunks = kbs.reduce((s, kb) => s + kb.total_chunks, 0)
  const fmtChunks = (n: number) => n >= 1_000_000 ? `${(n/1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n/1_000).toFixed(1)}k` : String(n)

  const filtered = useMemo(() =>
    search.trim()
      ? kbs.filter(kb =>
          kb.name.toLowerCase().includes(search.toLowerCase()) ||
          (kb.description ?? '').toLowerCase().includes(search.toLowerCase())
        )
      : kbs
  , [kbs, search])

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
          <button className="filter-tab active">
            All <span className="filter-count">{kbs.length}</span>
          </button>
          {kbs.some(k => !k.embedding_credential_id) && (
            <button className="filter-tab">
              Setup required <span className="filter-count">{kbs.filter(k => !k.embedding_credential_id).length}</span>
            </button>
          )}
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
