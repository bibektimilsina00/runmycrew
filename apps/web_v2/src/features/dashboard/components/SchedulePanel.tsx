import { Icons } from '@/shared/components'
import { PanelHead } from './PanelHead'

export interface ScheduleItem {
  time: string
  name: string
  sub: string
}

const defaultSchedule: ScheduleItem[] = [
  { time: '14:30', name: 'Weekly metrics digest', sub: 'linear · github · stripe' },
  { time: '16:00', name: 'Churn-risk watchlist refresh', sub: 'agent · 6 sources' },
  { time: '18:00', name: 'EOD pager rotation handoff', sub: 'pagerduty · slack' },
  { time: '02:00', name: 'Notion → Airtable sync', sub: 'scheduled · last failed' },
]

interface SchedulePanelProps {
  items?: ScheduleItem[]
  onOpenSchedule?: (item: ScheduleItem, index: number) => void
  onViewAll?: () => void
}

export function SchedulePanel({ items = defaultSchedule, onOpenSchedule, onViewAll }: SchedulePanelProps) {
  return (
    <div className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden flex flex-col">
      <PanelHead
        icon={<Icons.Clock className="w-3.5 h-3.5" />}
        title="Next 12 hours"
        action={
          onViewAll && (
            <button className="text-[12px] text-[var(--text-mute)] py-[4px] px-[8px] rounded-[6px] transition-colors duration-120 inline-flex items-center gap-[4px] hover:text-[var(--text)] hover:bg-[var(--surface)]" onClick={onViewAll}>
              <span>All</span>
              <Icons.CaretRight className="w-3 h-3" />
            </button>
          )
        }
      />
      <div>
        {items.map((s, i) => (
          <div key={i} className="flex items-center gap-[12px] py-[10px] px-[16px] border-b border-[var(--border-faint)] cursor-pointer transition-colors duration-100 last:border-b-0 hover:bg-[var(--surface)]" onClick={() => onOpenSchedule?.(s, i)}>
            <span className="font-mono text-[11px] text-[var(--text)] w-[56px] shrink-0">{s.time}</span>
            <span className="flex flex-col gap-[2px] min-w-0 flex-1">
              <span className="text-[12.5px] font-medium whitespace-nowrap overflow-hidden text-ellipsis">{s.name}</span>
              <span className="text-[11px] text-[var(--text-faint)] font-mono">{s.sub}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
