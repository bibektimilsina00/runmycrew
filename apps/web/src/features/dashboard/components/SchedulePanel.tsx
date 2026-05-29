import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components'
import { PanelHead } from './PanelHead'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { DashboardSchedule } from '../services/dashboardAPI'

interface Props {
  items: DashboardSchedule[]
  onViewAll: () => void
}

export function SchedulePanel({ items, onViewAll }: Props) {
  const navigate = useNavigate()

  return (
    <div className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden flex flex-col">
      <PanelHead
        icon={<Icons.Clock className="w-3.5 h-3.5" />}
        title="Next 12 hours"
        action={
          <button
            className="text-[12px] text-[var(--text-mute)] py-[4px] px-[8px] rounded-[6px] transition-colors inline-flex items-center gap-[4px] hover:text-[var(--text)] hover:bg-[var(--surface)]"
            onClick={onViewAll}
          >
            <span>All</span>
            <Icons.CaretRight className="w-3 h-3" />
          </button>
        }
      />
      {items.length === 0 ? (
        <div className="flex items-center gap-2 px-4 py-4 text-[12px] text-[var(--text-faint)]">
          <Icons.Clock className="w-4 h-4 text-[var(--text-dim)]" />
          No scheduled workflows in the next 12 hours.
        </div>
      ) : (
        <div>
          {items.map((s, i) => (
            <div
              key={i}
              className="flex items-center gap-[12px] py-[10px] px-[16px] border-b border-[var(--border-faint)] cursor-pointer transition-colors last:border-b-0 hover:bg-[var(--surface)]"
              onClick={() => navigate(APP_ROUTES.WORKFLOW(s.workflow_id))}
            >
              <span className="font-mono text-[11px] text-[var(--text)] w-[56px] shrink-0">{s.time}</span>
              <span className="flex flex-col gap-[2px] min-w-0 flex-1">
                <span className="text-[12.5px] font-medium whitespace-nowrap overflow-hidden text-ellipsis">{s.name}</span>
                <span className="text-[11px] text-[var(--text-faint)] font-mono">{s.sub}</span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
