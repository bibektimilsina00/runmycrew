import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { KnowledgeBase } from '../types/knowledgeTypes'

interface Props {
  items: KnowledgeBase[]
  onDelete: (kb: KnowledgeBase) => void
}

function fmtChunks(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return String(n)
}

function timeAgo(iso: string) {
  const d = Date.now() - new Date(iso).getTime()
  const days = Math.floor(d / 86400000)
  if (days === 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function KnowledgeList({ items, onDelete }: Props) {
  const navigate = useNavigate()
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-[var(--text-faint)]">
        <Icons.Book style={{ width: 24, height: 24, color: 'var(--text-dim)' }} />
        <span className="text-[13px]">No knowledge bases yet. Create one to get started.</span>
      </div>
    )
  }

  return (
    <div className="kn-grid">
      {items.map(kb => (
        <div key={kb.id} className="kn-card group cursor-pointer" onClick={() => navigate(APP_ROUTES.KNOWLEDGE_DETAIL(kb.id))}>
          <div className="kn-head">
            <span className="kn-kind">
              <Icons.Book style={{ width: 14, height: 14 }} />
            </span>
            <div className="flex items-center gap-2">
              {(() => {
                if (!kb.embedding_credential_id)
                  return <span className="kn-state stale">not configured</span>
                if (kb.document_count === 0)
                  return <span className="kn-state stale">empty</span>
                if (kb.total_chunks === 0)
                  return <span className="kn-state stale">needs indexing</span>
                return <span className="kn-state indexed">indexed</span>
              })()}
              <button
                className="w-[22px] h-[22px] rounded-[5px] flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[oklch(0.70_0.18_22/0.14)] hover:text-[var(--err)] transition-all"
                onClick={e => { e.stopPropagation(); onDelete(kb) }}
                title="Delete knowledge base"
              >
                <Icons.Trash style={{ width: 12, height: 12 }} />
              </button>
            </div>
          </div>

          <div className="kn-body">
            <div className="kn-name">{kb.name}</div>
            <div className="kn-meta-row">
              {kb.description
                ? <span className="text-[var(--text-faint)] text-[12px]">{kb.description}</span>
                : <><span>{fmtChunks(kb.total_chunks)} chunks</span><span>·</span><span className="font-mono truncate">{kb.embedding_model}</span></>
              }
            </div>
          </div>

          <div className="kn-foot">
            <div className="kn-usage">
              <div className="kn-usage-bar">
                <span style={{ width: `${Math.min((kb.total_chunks / 10000) * 100, 100)}%` }} />
              </div>
              <span className="kn-usage-num">{fmtChunks(kb.total_chunks)} chunks indexed</span>
            </div>
            <span className="kn-updated">{timeAgo(kb.created_at)}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
