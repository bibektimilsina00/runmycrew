import { Icons } from '@/shared/components/icons'
import { Empty } from '@/shared/components'
import type { Run } from '../types/runsTypes'

interface Props {
  items: Run[]
  totalCount?: number
}

export function RunsTable({ items, totalCount = 0 }: Props) {
  if (items.length === 0) {
    return (
      <div className="panel">
        <Empty
          icon={<Icons.Activity />}
          title="No runs found"
          description={
            totalCount === 0
              ? 'Run automation workflows to see execution history here.'
              : 'No runs match the current filter.'
          }
          className="flex-1 justify-center"
        />
      </div>
    )
  }

  return (
    <div className="panel">
      <div className="table runs-table">
        <div className="table-head">
          <span></span>
          <span>Automation</span>
          <span>Trigger</span>
          <span>Started</span>
          <span>Duration</span>
          <span></span>
        </div>
        {items.map(r => (
          <div key={r.id} className="table-row">
            <span className={`status-dot ${r.status}`} />
            <span className="row-name">{r.name}</span>
            <span className="run-trigger"><Icons.Bolt />{r.trigger}</span>
            <span className="row-mono">{r.started}</span>
            <span className="row-mono">{r.duration}</span>
            <span className="caret"><Icons.CaretRight /></span>
          </div>
        ))}
      </div>
    </div>
  )
}
