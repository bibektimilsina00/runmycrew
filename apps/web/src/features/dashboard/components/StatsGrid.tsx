import React from 'react'
import { Icons } from '@/shared/components'
import { Sparkline } from './Sparkline'
import { cn } from '@/lib/cn'
import type { DashboardStat } from '../services/dashboardAPI'

const STAT_ICONS: Record<string, React.ReactNode> = {
  'Runs today':       <Icons.Activity className="w-3.5 h-3.5" />,
  'Success rate':     <Icons.Check    className="w-3.5 h-3.5" />,
  'Time saved':       <Icons.Clock    className="w-3.5 h-3.5" />,
  'Active workflows': <Icons.Layers   className="w-3.5 h-3.5" />,
}

interface Props { items: DashboardStat[] }

export function StatsGrid({ items }: Props) {
  return (
    <div className="grid grid-cols-4 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden">
      {items.map((s, i) => (
        <div key={i} className="pt-[16px] px-[18px] pb-[18px] border-r border-[var(--border-faint)] flex flex-col gap-[6px] relative last:border-r-0">
          <span className="text-[12px] text-[var(--text-mute)] flex items-center gap-[7px]">
            {STAT_ICONS[s.label] ?? <Icons.Activity className="w-3.5 h-3.5" />}
            <span>{s.label}</span>
          </span>
          <span className="text-[26px] font-medium tracking-tight text-[var(--text)] mt-[2px]">
            {s.value}
            {s.unit && <span className="text-[14px] text-[var(--text-faint)] ml-[3px]">{s.unit}</span>}
          </span>
          <span className={cn(
            "font-mono text-[11px] inline-flex items-center gap-[4px]",
            s.delta_dir === 'up'   && 'text-emerald-500',
            s.delta_dir === 'down' && 'text-red-500',
            s.delta_dir === 'flat' && 'text-[var(--text-dim)]'
          )}>
            {s.delta_dir === 'up' ? '↑' : s.delta_dir === 'down' ? '↓' : '—'} {s.delta}
          </span>
          <Sparkline
            data={s.spark}
            color={s.delta_dir === 'down' ? '#ef4444' : '#10b981'}
            className="absolute right-[14px] top-[14px] w-[70px] h-[28px] opacity-[0.85]"
          />
        </div>
      ))}
    </div>
  )
}
