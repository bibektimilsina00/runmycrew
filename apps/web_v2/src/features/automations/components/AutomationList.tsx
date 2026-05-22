import { Icons } from '@/shared/components/icons'
import type { Automation } from '../types/automationsTypes'

interface Props { items: Automation[] }

export function AutomationList({ items }: Props) {
  return (
    <div className="panel">
      <div className="table">
        <div className="table-head">
          <span></span>
          <span>Name</span>
          <span>Kind</span>
          <span>Runs</span>
          <span>Last run</span>
          <span>Owner</span>
          <span>Status</span>
          <span></span>
        </div>
        {items.map(a => (
          <div key={a.id} className="table-row">
            <span className={`status-dot ${a.status === 'error' ? 'err' : a.status === 'paused' ? 'warn' : a.status === 'draft' ? 'draft' : 'ok'}`} />
            <span className="row-name">{a.name}</span>
            <span className="row-kind">
              {a.kind === 'agent' ? <Icons.Spark /> : a.kind === 'schedule' ? <Icons.Clock /> : <Icons.Flow />}
              {a.kind}
            </span>
            <span className="row-mono">{a.runs}</span>
            <span className="row-mono">{a.last}</span>
            <span className="row-owner">{a.owner}</span>
            <span className={`status-pill ${a.status === 'error' ? 'err' : a.status === 'paused' ? 'warn' : a.status === 'draft' ? 'draft' : 'ok'}`}>
              {a.status}
            </span>
            <span className="caret"><Icons.CaretRight /></span>
          </div>
        ))}
      </div>
    </div>
  )
}
