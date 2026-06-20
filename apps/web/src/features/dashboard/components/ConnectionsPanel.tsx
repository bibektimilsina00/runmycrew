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

const STATE_LABEL: Record<DashboardConnection['state'], string> = { ok: 'OK', warn: 'Warn', err: 'Error' }
const STATE_TONE: Record<DashboardConnection['state'], { bg: string; text: string; dot: string }> = {
  ok:   { bg: 'var(--badge-ok-bg)',   text: 'var(--ok)',   dot: 'var(--ok)' },
  warn: { bg: 'var(--badge-warn-bg)', text: 'var(--warn)', dot: 'var(--warn)' },
  err:  { bg: 'var(--badge-err-bg)',  text: 'var(--err)',  dot: 'var(--err)' },
}

function providerInitial(type: string): string {
  return type.replace('_oauth', '').replace('_api_key', '').slice(0, 2).toUpperCase()
}

export function ConnectionsPanel({ items, totalActive }: Props) {
  const navigate = useNavigate()
  const { data: providers = [] } = useProviders()
  const providerMap = Object.fromEntries(providers.map(p => [p.id, p]))

  return (
    <div className="border border-[var(--border-faint)] rounded-[8px] bg-[var(--surface)] overflow-hidden flex flex-col">
      <PanelHead
        icon={<Icons.Plug />}
        title="Connections"
        count={`${totalActive} active`}
        countTone="ok"
        action={
          <button
            className="text-[12px] font-medium text-[var(--text-faint)] py-[4px] px-[8px] rounded-[6px] transition-colors inline-flex items-center gap-[4px] hover:text-[var(--text)] hover:bg-[rgba(255,255,255,0.05)]"
            onClick={() => navigate(APP_ROUTES.CONNECTIONS)}
          >
            Manage
            <Icons.CaretRight className="w-[13px] h-[13px]" />
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
        <div className="flex flex-col gap-[2px] pb-[8px] px-[8px]">
          {items.map(c => {
            const provider = providerMap[c.type]
            const iconUrl  = provider?.icon_url
            const initial  = provider?.name?.slice(0, 2).toUpperCase() ?? providerInitial(c.type)
            const tone     = STATE_TONE[c.state]
            return (
              <button
                key={c.id}
                onClick={() => navigate(APP_ROUTES.CONNECTIONS)}
                className="w-full flex items-center gap-[11px] py-[8px] px-[12px] rounded-[6px] bg-transparent text-left transition-colors cursor-pointer hover:bg-[rgba(255,255,255,0.04)]"
              >
                {iconUrl ? (
                  <img
                    src={iconUrl}
                    alt={provider?.name ?? c.type}
                    className="w-[30px] h-[30px] rounded-[8px] object-contain bg-[var(--surface-2)] p-1 shrink-0"
                    onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                ) : (
                  <span className="w-[30px] h-[30px] rounded-[8px] inline-flex items-center justify-center text-[13px] font-bold text-white shrink-0 bg-[linear-gradient(135deg,var(--surface-3),var(--surface-2))]">
                    {initial}
                  </span>
                )}
                <span className="flex flex-col gap-[2px] min-w-0 flex-1 leading-[1.3]">
                  <span className="text-[13px] font-medium text-[var(--text)] truncate">{c.name}</span>
                  <span className="text-[11px] text-[var(--text-faint)] truncate">{provider?.name ?? c.type}</span>
                </span>
                <span
                  className={cn('inline-flex items-center gap-[5px] text-[11px] font-semibold rounded-[6px] py-[3px] px-[8px]')}
                  style={{ background: tone.bg, color: tone.text }}
                >
                  <span className="w-[5px] h-[5px] rounded-full" style={{ background: tone.dot }} />
                  {STATE_LABEL[c.state]}
                </span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
