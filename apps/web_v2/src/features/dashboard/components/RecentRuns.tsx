import { Icons } from '@/shared/components'
import { PanelHead } from './PanelHead'

export interface RunItem {
  status: 'ok' | 'run' | 'err' | 'warn'
  name: string
  trigger: string
  duration: string
  ago: string
}

const defaultRuns: RunItem[] = [
  { status: 'ok', name: 'Stripe refund — Slack approval', trigger: 'stripe.charge.refunded', duration: '1.4s', ago: '2m ago' },
  { status: 'ok', name: 'Lead enrichment — Clearbit → HubSpot', trigger: 'hubspot.contact.created', duration: '3.1s', ago: '4m ago' },
  { status: 'run', name: 'Inbound RFP classifier', trigger: 'imap.inbox.new', duration: 'running', ago: 'now' },
  { status: 'ok', name: 'Daily brief from Linear + GitHub', trigger: 'schedule.daily', duration: '8.7s', ago: '1h ago' },
  { status: 'err', name: 'Notion → Airtable nightly sync', trigger: 'schedule.0_2_*_*_*', duration: '12.4s', ago: '2h ago' },
  { status: 'ok', name: 'Invoice triage agent', trigger: 'gmail.label.invoice', duration: '5.9s', ago: '3h ago' },
  { status: 'warn', name: 'Support ticket auto-tagger', trigger: 'zendesk.ticket.new', duration: '2.2s', ago: '4h ago' },
  { status: 'ok', name: 'Weekly metrics digest', trigger: 'schedule.weekly', duration: '11.0s', ago: '5h ago' },
]

interface RecentRunsProps {
  items?: RunItem[]
  onOpenRun: (run: RunItem, index: number) => void
  onViewAll: () => void
}

export function RecentRuns({ items = defaultRuns, onOpenRun, onViewAll }: RecentRunsProps) {
  return (
    <div className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden flex flex-col">
      <PanelHead
        icon={<Icons.Activity className="w-3.5 h-3.5" />}
        title="Recent runs"
        count="1,284 today"
        action={
          <button className="text-[12px] text-[var(--text-mute)] py-[4px] px-[8px] rounded-[6px] transition-colors duration-120 inline-flex items-center gap-[4px] hover:text-[var(--text)] hover:bg-[var(--surface)]" onClick={onViewAll}>
            <span>View all</span>
            <Icons.CaretRight className="w-3 h-3" />
          </button>
        }
      />
      <div className="flex flex-col">
        {items.map((r, i) => (
          <div key={i} className="grid grid-cols-[22px_1fr_180px_80px_80px_22px] gap-[12px] items-center py-[10px] px-[16px] border-b border-[var(--border-faint)] text-[13px] cursor-pointer transition-colors duration-100 last:border-b-0 hover:bg-[var(--surface)]" onClick={() => onOpenRun(r, i)}>
            <span className={`status-dot ${r.status}`} />
            <span className="font-medium whitespace-nowrap overflow-hidden text-ellipsis">{r.name}</span>
            <span className="inline-flex items-center gap-[6px] font-mono text-[11px] text-[var(--text-mute)]">
              <Icons.Bolt className="w-2.5 h-2.5" />
              <span>{r.trigger}</span>
            </span>
            <span className="font-mono text-[11px] text-[var(--text-faint)]">{r.duration}</span>
            <span className="font-mono text-[11px] text-[var(--text-faint)]">{r.ago}</span>
            <span className="text-[var(--text-dim)] inline-flex">
              <Icons.CaretRight className="w-3.5 h-3.5" />
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
