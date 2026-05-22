import { Icons } from '@/shared/components/icons'
import type { KnowledgeSource, KnowledgeKind } from '../types/knowledgeTypes'

interface Props { items: KnowledgeSource[] }

function KindIcon({ kind }: { kind: KnowledgeKind }) {
  switch (kind) {
    case 'site':   return <Icons.Globe />
    case 'slack':  return <Icons.Slack />
    case 'notion': return <Icons.Book />
    case 'linear': return <Icons.Layers />
    case 'csv':    return <Icons.Table />
    default:       return <Icons.Doc />
  }
}

export function KnowledgeList({ items }: Props) {
  return (
    <div className="kn-grid">
      {items.map(k => (
        <div key={k.id} className="kn-card">
          <div className="kn-head">
            <span className="kn-kind"><KindIcon kind={k.kind} /></span>
            <span className={`kn-state ${k.state}`}>{k.state}</span>
          </div>
          <div className="kn-body">
            <div className="kn-name">{k.name}</div>
            <div className="kn-meta-row">
              <span>{k.items} {k.items === 1 ? 'item' : 'items'}</span>
              <span>·</span>
              <span>{k.tokens} tokens</span>
            </div>
          </div>
          <div className="kn-foot">
            <div className="kn-usage">
              <div className="kn-usage-bar">
                <span style={{ width: `${k.used}%` }} />
              </div>
              <span className="kn-usage-num">{k.used}% usage</span>
            </div>
            <span className="kn-updated">{k.updated}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
