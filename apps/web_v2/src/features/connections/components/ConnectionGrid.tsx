import type { Connection } from '../types/connectionsTypes'

interface Props { items: Connection[] }

export function ConnectionGrid({ items }: Props) {
  return (
    <div className="conn-grid">
      {items.map(c => (
        <div key={c.id} className="conn-card">
          <div className="conn-card-head">
            <span className={`conn-icon ${c.id}`}>{c.name.slice(0, 2)}</span>
            <span className={`conn-state ${c.state}`}>{c.state}</span>
          </div>
          <div className="conn-card-body">
            <div className="conn-card-name">{c.name}</div>
            <div className="conn-card-sub">{c.sub}</div>
          </div>
          <div className="conn-card-foot">
            <span>{c.endpoints} endpoints</span>
            <span>{c.last}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
