import React from 'react'
import { Icons } from '@/shared/components'
import { Sparkline } from './Sparkline'
import { cn } from '@/lib/cn'
import type { DashboardStat } from '../services/dashboardAPI'

const STAT_ICONS: Record<string, React.ReactNode> = {
  'Runs today':       <Icons.Activity />,
  'Success rate':     <Icons.Check />,
  'Time saved':       <Icons.Clock />,
  'Active workflows': <Icons.Layers />,
}

interface Props { items: DashboardStat[] }

export function StatsGrid({ items }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-[16px]">
      {items.map((s, i) => {
        const trendColor =
          s.delta_dir === 'up'   ? 'var(--ok)' :
          s.delta_dir === 'down' ? 'var(--err)' :
                                   'var(--text-dim)'

        return (
          <div
            key={i}
            className="border border-[var(--border-soft)] bg-[rgba(255,255,255,0.018)] rounded-[10px] py-[14px] px-[16px] flex flex-col"
          >
            <div className="flex items-start justify-between">
              <div className="inline-flex items-center gap-[8px] text-[var(--text-mute)] [&_svg]:w-[15px] [&_svg]:h-[15px]">
                {STAT_ICONS[s.label] ?? <Icons.Activity />}
                <span className="text-[11.5px] font-medium">{s.label}</span>
              </div>
              <Sparkline
                data={s.spark}
                color={s.delta_dir === 'down' ? 'var(--err)' : 'var(--ok)'}
                className="w-[58px] h-[19px]"
              />
            </div>
            <div className="flex items-baseline gap-[3px] mt-[9px]">
              <span className="font-mono text-[24px] font-semibold tracking-[-0.02em] text-[var(--text)]">
                {s.value}
              </span>
              {s.unit && (
                <span className="text-[13px] text-[var(--text-faint)] font-medium">{s.unit}</span>
              )}
            </div>
            <div
              className={cn(
                'inline-flex items-center gap-[5px] mt-[6px] text-[11.5px] font-semibold',
                s.delta_dir === 'flat' && 'text-[var(--text-faint)] font-medium',
              )}
              style={{ color: trendColor }}
            >
              {s.delta_dir === 'flat' ? (
                <span className="font-mono">+0</span>
              ) : (
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  {s.delta_dir === 'up' ? (
                    <>
                      <line x1="12" y1="19" x2="12" y2="5" />
                      <polyline points="6 11 12 5 18 11" />
                    </>
                  ) : (
                    <>
                      <line x1="12" y1="5" x2="12" y2="19" />
                      <polyline points="6 13 12 19 18 13" />
                    </>
                  )}
                </svg>
              )}
              <span>{s.delta}</span>
              <span className="text-[var(--text-dim)] font-medium">
                {s.delta_dir === 'flat' ? 'no change' : 'vs yesterday'}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
