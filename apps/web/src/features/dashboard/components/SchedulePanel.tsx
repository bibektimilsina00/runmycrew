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
    <div className="border border-[var(--border-faint)] rounded-[8px] bg-[var(--surface)] overflow-hidden flex flex-col">
      <PanelHead
        icon={<Icons.Clock />}
        title="Next 12 hours"
        action={
          <button
            className="text-[12px] font-medium text-[var(--text-faint)] py-[4px] px-[8px] rounded-[6px] transition-colors inline-flex items-center gap-[4px] hover:text-[var(--text)] hover:bg-[rgba(255,255,255,0.05)]"
            onClick={onViewAll}
          >
            All
            <Icons.CaretRight className="w-[13px] h-[13px]" />
          </button>
        }
      />
      {items.length === 0 ? (
        <div className="py-[26px] px-[15px] flex flex-col items-center gap-[9px] text-center">
          <div className="w-[36px] h-[36px] rounded-[10px] border border-[var(--border-soft)] bg-[rgba(255,255,255,0.03)] inline-flex items-center justify-center text-[var(--text-dim)]">
            <Icons.Clock className="w-[18px] h-[18px]" />
          </div>
          <span className="text-[12.5px] text-[var(--text-faint)]">No scheduled workflows in the next 12 hours.</span>
        </div>
      ) : (
        <div className="flex flex-col gap-[2px] pb-[8px] px-[8px]">
          {items.map((s, i) => (
            <button
              key={i}
              onClick={() => navigate(APP_ROUTES.WORKFLOW(s.workflow_id))}
              className="w-full flex items-center gap-[12px] py-[8px] px-[12px] rounded-[6px] bg-transparent text-left transition-colors cursor-pointer hover:bg-[rgba(255,255,255,0.04)]"
            >
              <span className="font-mono text-[11.5px] text-[var(--text)] w-[54px] shrink-0">{s.time}</span>
              <span className="flex flex-col gap-[2px] min-w-0 flex-1">
                <span className="text-[12.5px] font-medium text-[var(--text)] truncate">{s.name}</span>
                <span className="text-[11px] text-[var(--text-faint)] font-mono truncate">{s.sub}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
