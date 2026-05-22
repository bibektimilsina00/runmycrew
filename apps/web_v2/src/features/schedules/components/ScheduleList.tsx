import { Icons } from '@/shared/components/icons'
import type { Schedule } from '../types/schedulesTypes'

interface Props { items: Schedule[] }

export function ScheduleList({ items }: Props) {
  return (
    <div className="panel">
      <div className="table table-sched">
        <div className="table-head">
          <span></span>
          <span>Name</span>
          <span>Cron</span>
          <span>Next run</span>
          <span>Last run</span>
          <span>Status</span>
          <span></span>
        </div>
        {items.map(s => (
          <div key={s.id} className="table-row">
            <span className={`status-dot ${s.state === 'error' ? 'err' : s.state === 'paused' ? 'warn' : 'ok'}`} />
            <span className="row-name">{s.name}</span>
            <span className="row-mono">{s.cron}</span>
            <span className="row-mono"><Icons.Clock style={{ width: 11, height: 11, marginRight: 5 }} />{s.next}</span>
            <span className="row-mono">{s.last}</span>
            <span className={`status-pill ${s.state === 'error' ? 'err' : s.state === 'paused' ? 'warn' : 'ok'}`}>
              {s.state}
            </span>
            <span className="caret"><Icons.CaretRight /></span>
          </div>
        ))}
      </div>
    </div>
  )
}
