import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components'
import { PanelHead } from './PanelHead'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { DashboardRun } from '../services/dashboardAPI'

interface Props {
  items: DashboardRun[]
  totalToday: number
  onViewAll: () => void
}

export function RecentRuns({ items, totalToday, onViewAll }: Props) {
  const navigate = useNavigate()

  return (
    <div className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden flex flex-col">
      <PanelHead
        icon={<Icons.Activity className="w-3.5 h-3.5" />}
        title="Recent runs"
        count={`${totalToday.toLocaleString()} today`}
        action={
          <button
            className="text-[12px] text-[var(--text-mute)] py-[4px] px-[8px] rounded-[6px] transition-colors inline-flex items-center gap-[4px] hover:text-[var(--text)] hover:bg-[var(--surface)]"
            onClick={onViewAll}
          >
            <span>View all</span>
            <Icons.CaretRight className="w-3 h-3" />
          </button>
        }
      />
      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 py-10 text-[var(--text-faint)]">
          <Icons.Activity className="w-5 h-5 text-[var(--text-dim)]" />
          <span className="text-[13px]">No runs yet. Trigger an automation to see results here.</span>
        </div>
      ) : (
        <div className="flex flex-col">
          {items.map(r => (
            <div
              key={r.id}
              className="grid grid-cols-[22px_1fr_180px_80px_80px_22px] gap-[12px] items-center py-[10px] px-[16px] border-b border-[var(--border-faint)] text-[13px] cursor-pointer transition-colors last:border-b-0 hover:bg-[var(--surface)]"
              onClick={() => navigate(APP_ROUTES.RUNS)}
            >
              <span className={`status-dot ${r.status}`} />
              <span className="font-medium whitespace-nowrap overflow-hidden text-ellipsis">{r.name}</span>
              <span className="inline-flex items-center gap-[6px] font-mono text-[11px] text-[var(--text-mute)]">
                <Icons.Bolt className="w-2.5 h-2.5" />
                <span className="truncate">{r.trigger}</span>
              </span>
              <span className="font-mono text-[11px] text-[var(--text-faint)]">{r.duration}</span>
              <span className="font-mono text-[11px] text-[var(--text-faint)]">{r.ago}</span>
              <span className="text-[var(--text-dim)] inline-flex">
                <Icons.CaretRight className="w-3.5 h-3.5" />
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
