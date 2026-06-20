import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components'
import { cn } from '@/lib/cn'
import { PanelHead } from './PanelHead'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { DashboardRun } from '../services/dashboardAPI'

interface Props {
  items: DashboardRun[]
  totalToday: number
  onViewAll: () => void
}

const STATUS_DOT: Record<DashboardRun['status'], { dot: string; glow: string }> = {
  ok:   { dot: 'var(--ok)',   glow: 'rgba(76,195,138,0.18)' },
  run:  { dot: 'var(--accent)', glow: 'var(--accent-soft)' },
  err:  { dot: 'var(--err)',  glow: 'rgba(229,103,95,0.20)' },
  warn: { dot: 'var(--warn)', glow: 'rgba(231,183,102,0.20)' },
}

export function RecentRuns({ items, totalToday, onViewAll }: Props) {
  const navigate = useNavigate()

  return (
    <div className="border border-[var(--border-faint)] rounded-[8px] bg-[var(--surface)] overflow-hidden flex flex-col">
      <PanelHead
        icon={<Icons.Activity />}
        title="Recent runs"
        count={`${totalToday.toLocaleString()} today`}
        action={
          <button
            className="text-[12px] font-medium text-[var(--text-faint)] py-[4px] px-[8px] rounded-[6px] transition-colors inline-flex items-center gap-[4px] hover:text-[var(--text)] hover:bg-[rgba(255,255,255,0.05)]"
            onClick={onViewAll}
          >
            View all
            <Icons.CaretRight className="w-[13px] h-[13px]" />
          </button>
        }
      />
      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 py-10 text-[var(--text-faint)]">
          <Icons.Activity className="w-5 h-5 text-[var(--text-dim)]" />
          <span className="text-[13px]">No runs yet. Trigger an automation to see results here.</span>
        </div>
      ) : (
        <div className="flex flex-col gap-[2px] pb-[8px] px-[8px]">
          {items.map(r => {
            const tone = STATUS_DOT[r.status] ?? STATUS_DOT.ok
            return (
              <button
                key={r.id}
                onClick={() => navigate(APP_ROUTES.RUNS)}
                className={cn(
                  'w-full flex items-center gap-[12px] py-[8px] px-[12px] rounded-[6px] bg-transparent text-left transition-colors cursor-pointer',
                  'hover:bg-[rgba(255,255,255,0.04)]',
                )}
              >
                <span
                  className="w-[8px] h-[8px] rounded-full shrink-0"
                  style={{ background: tone.dot, boxShadow: `0 0 0 3px ${tone.glow}` }}
                />
                <span className="text-[13px] text-[var(--text)] font-medium flex-1 min-w-0 truncate">{r.name}</span>
                <span className="font-mono text-[11.5px] text-[var(--text-mute)] bg-[rgba(255,255,255,0.04)] border border-[var(--border-soft)] rounded-[5px] py-[2px] px-[7px]">
                  {r.trigger}
                </span>
                <span className="font-mono text-[11.5px] text-[var(--text-faint)] w-[54px] text-right">{r.duration}</span>
                <span className="text-[11.5px] text-[var(--text-dim)] w-[48px] text-right">{r.ago}</span>
                <Icons.CaretRight className="w-[14px] h-[14px] text-[var(--text-dim)] shrink-0" />
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
