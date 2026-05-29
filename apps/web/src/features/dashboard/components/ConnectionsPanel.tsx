import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components'
import { cn } from '@/lib/cn'
import { PanelHead } from './PanelHead'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useProviders } from '@/features/connections/hooks/useConnections'
import type { DashboardConnection } from '../services/dashboardAPI'

interface Props {
  items: DashboardConnection[]
  totalActive: number
}

function providerInitial(type: string): string {
  return type.replace('_oauth', '').replace('_api_key', '').slice(0, 2).toUpperCase()
}

export function ConnectionsPanel({ items, totalActive }: Props) {
  const navigate = useNavigate()
  const { data: providers = [] } = useProviders()
  const providerMap = Object.fromEntries(providers.map(p => [p.id, p]))

  return (
    <div className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden flex flex-col">
      <PanelHead
        icon={<Icons.Plug className="w-3.5 h-3.5" />}
        title="Connections"
        count={`${totalActive} active`}
        action={
          <button
            className="text-[12px] text-[var(--text-mute)] py-[4px] px-[8px] rounded-[6px] transition-colors inline-flex items-center gap-[4px] hover:text-[var(--text)] hover:bg-[var(--surface)]"
            onClick={() => navigate(APP_ROUTES.CONNECTIONS)}
          >
            <span>Manage</span>
            <Icons.CaretRight className="w-3 h-3" />
          </button>
        }
      />
      {items.length === 0 ? (
        <div className="flex items-center gap-2 px-4 py-4 text-[12px] text-[var(--text-faint)]">
          <Icons.Plug className="w-4 h-4 text-[var(--text-dim)]" />
          No connections yet.{' '}
          <button className="underline" onClick={() => navigate(APP_ROUTES.CONNECTIONS)}>Add one</button>
        </div>
      ) : (
        <div>
          {items.map(c => {
            const provider = providerMap[c.type]
            const iconUrl  = provider?.icon_url
            const initial  = provider?.name?.slice(0, 2).toUpperCase() ?? providerInitial(c.type)

            return (
              <div
                key={c.id}
                className="flex items-center gap-[12px] py-[10px] px-[16px] border-b border-[var(--border-faint)] last:border-b-0 cursor-pointer hover:bg-[var(--surface)] transition-colors"
                onClick={() => navigate(APP_ROUTES.CONNECTIONS)}
              >
                {iconUrl ? (
                  <img
                    src={iconUrl}
                    alt={provider?.name ?? c.type}
                    className="w-[28px] h-[28px] rounded-[7px] object-contain bg-[var(--surface)] p-1 shrink-0"
                    onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                ) : (
                  <span className="w-[28px] h-[28px] rounded-[7px] inline-flex items-center justify-center text-[11px] font-semibold shrink-0 bg-[var(--surface-3)] text-[var(--text)]">
                    {initial}
                  </span>
                )}
                <span className="flex flex-col gap-[2px] min-w-0 flex-1">
                  <span className="text-[12.5px] font-medium whitespace-nowrap overflow-hidden text-ellipsis">{c.name}</span>
                  <span className="text-[11px] text-[var(--text-faint)] font-mono">{provider?.name ?? c.type}</span>
                </span>
                <span className={cn(
                  "font-mono text-[10px] tracking-widest uppercase py-[3px] px-[7px] pb-[2px] rounded-[4px] font-medium",
                  c.state === 'ok'   && 'bg-emerald-500/15 text-emerald-500',
                  c.state === 'warn' && 'bg-amber-500/15 text-amber-500',
                  c.state === 'err'  && 'bg-red-500/15 text-red-500',
                )}>{c.state}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
