import { Icons } from '@/shared/components/icons'
import { Empty } from '@/shared/components'
import type { LogEntry } from '../types/logsTypes'

const LVL_LABEL: Record<string, string> = { err: 'ERR', warn: 'WARN', info: 'INFO' }

interface Props {
  items: LogEntry[]
  totalCount?: number
}

export function LogStream({ items, totalCount = 0 }: Props) {
  if (items.length === 0) {
    return (
      <div className="panel">
        <Empty
          icon={<Icons.Terminal />}
          title="No logs found"
          description={
            totalCount === 0
              ? 'Workflow execution logs will appear here.'
              : 'No logs match the current filter.'
          }
          className="flex-1 justify-center"
        />
      </div>
    )
  }

  return (
    <div className="panel logs-panel">
      <div className="log-stream">
        {items.map((l) => {
          const label = LVL_LABEL[l.lvl] ?? 'INFO'
          const lineClass = l.lvl === 'err' ? ' err' : l.lvl === 'warn' ? ' warn' : ''
          return (
            <div key={l.id} className={`log-line${lineClass}`}>
              <span className="log-time">{l.t}</span>
              <span className={`log-lvl ${label}`}>{label}</span>
              <span className="log-src">{l.src}</span>
              <span className="log-msg" title={l.msg}>{l.msg}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
