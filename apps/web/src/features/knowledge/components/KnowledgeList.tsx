import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'
import { isKBConfigured, type KnowledgeBase } from '../types/knowledgeTypes'

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
  if (items.length === 0) return null

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
                if (!isKBConfigured(kb))
                  return <span className="kn-state stale">not configured</span>
                if (kb.document_count === 0)
                  return <span className="kn-state stale">empty</span>
                if (kb.total_chunks === 0)
                  return <span className="kn-state stale">needs indexing</span>
                return <span className="kn-state indexed">indexed</span>
              })()}
              <button
                className="w-[22px] h-[22px] rounded-[5px] flex items-center justify-center text-[var(--text-dim)] hover:bg-[oklch(0.70_0.18_22/0.14)] hover:text-[var(--err)] transition-colors"
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
                : <span className="font-mono truncate text-[12px] text-[var(--text-faint)]">{kb.embedding_model}</span>
              }
            </div>
          </div>

          <div className="kn-foot">
            <span className="kn-usage-num">
              {fmtChunks(kb.document_count)} {kb.document_count === 1 ? 'doc' : 'docs'} ·{' '}
              {fmtChunks(kb.total_chunks)} {kb.total_chunks === 1 ? 'chunk' : 'chunks'}
            </span>
            <span className="kn-updated">{timeAgo(kb.created_at)}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
