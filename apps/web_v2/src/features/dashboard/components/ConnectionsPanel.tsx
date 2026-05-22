import { Icons } from '@/shared/components'
import { cn } from '@/lib/cn'
import { PanelHead } from './PanelHead'

export interface ConnectionItem {
  id: string
  name: string
  sub: string
  state: 'ok' | 'warn' | 'err'
}

const defaultConnections: ConnectionItem[] = [
  { id: 'stripe', name: 'Stripe', sub: '12 endpoints · 4 webhooks', state: 'ok' },
  { id: 'slack', name: 'Slack', sub: '3 workspaces', state: 'ok' },
  { id: 'linear', name: 'Linear', sub: 'fuse-engineering', state: 'ok' },
  { id: 'notion', name: 'Notion', sub: 'token expires in 4d', state: 'warn' },
  { id: 'hub', name: 'HubSpot', sub: 'auth failed · re-link', state: 'err' },
]

interface ConnectionsPanelProps {
  items?: ConnectionItem[]
  onManageConnections: () => void
}

export function ConnectionsPanel({ items = defaultConnections, onManageConnections }: ConnectionsPanelProps) {
  return (
    <div className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden flex flex-col">
      <PanelHead
        icon={<Icons.Plug className="w-3.5 h-3.5" />}
        title="Connections"
        count="18 active"
        action={
          <button className="text-[12px] text-[var(--text-mute)] py-[4px] px-[8px] rounded-[6px] transition-colors duration-120 inline-flex items-center gap-[4px] hover:text-[var(--text)] hover:bg-[var(--surface)]" onClick={onManageConnections}>
            <span>Manage</span>
            <Icons.CaretRight className="w-3 h-3" />
          </button>
        }
      />
      <div>
        {items.map((c, i) => (
          <div key={i} className="flex items-center gap-[12px] py-[10px] px-[16px] border-b border-[var(--border-faint)] last:border-b-0">
            <span className={cn(
              "w-[28px] h-[28px] rounded-[7px] inline-flex items-center justify-center text-[11px] font-semibold shrink-0 text-white tracking-tight",
              c.id === 'stripe' && "bg-gradient-to-br from-indigo-500 to-indigo-700",
              c.id === 'slack' && "bg-gradient-to-br from-amber-500 to-amber-700",
              c.id === 'linear' && "bg-gradient-to-br from-blue-500 to-blue-700",
              c.id === 'notion' && "bg-gradient-to-br from-zinc-600 to-zinc-800",
              c.id === 'hub' && "bg-gradient-to-br from-orange-500 to-orange-700"
            )}>
              {c.name.slice(0, 2)}
            </span>
            <span className="flex flex-col gap-[2px] min-w-0 flex-1">
              <span className="text-[12.5px] font-medium whitespace-nowrap overflow-hidden text-ellipsis">{c.name}</span>
              <span className="text-[11px] text-[var(--text-faint)] font-mono">{c.sub}</span>
            </span>
            <span className={cn(
              "font-mono text-[10px] tracking-widest uppercase py-[3px] px-[7px] pb-[2px] rounded-[4px] font-medium",
              c.state === 'ok' && "bg-emerald-500/15 text-emerald-500",
              c.state === 'warn' && "bg-amber-500/15 text-amber-500",
              c.state === 'err' && "bg-red-500/15 text-red-500"
            )}>{c.state}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
