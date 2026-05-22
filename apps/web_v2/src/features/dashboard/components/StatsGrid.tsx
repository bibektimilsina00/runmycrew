import React from 'react'
import { Icons } from '@/shared/components'
import { Sparkline } from './Sparkline'
import { cn } from '@/lib/cn'

export interface StatItem {
  label: string
  value: string
  unit: string
  delta: string
  deltaDir: 'up' | 'down' | 'flat'
  spark: number[]
  icon: React.ReactNode
}

const defaultStats: StatItem[] = [
  { label: 'Runs today', value: '1,284', unit: '', delta: '+18%', deltaDir: 'up', spark: [4, 5, 3, 6, 4, 7, 8, 6, 9, 11, 9, 12], icon: <Icons.Activity className="w-3.5 h-3.5" /> },
  { label: 'Success rate', value: '99.2', unit: '%', delta: '+0.4pp', deltaDir: 'up', spark: [98, 97.8, 98.2, 98.5, 98.6, 99, 99.1, 99.2, 99.1, 99.2, 99.2, 99.2], icon: <Icons.Check className="w-3.5 h-3.5" /> },
  { label: 'Time saved', value: '14.2', unit: 'hr', delta: '+2.1hr', deltaDir: 'up', spark: [6, 7, 8, 8, 9, 10, 11, 12, 13, 13, 14, 14.2], icon: <Icons.Clock className="w-3.5 h-3.5" /> },
  { label: 'Active steps', value: '312', unit: '', delta: '-4', deltaDir: 'down', spark: [340, 338, 336, 334, 330, 324, 320, 318, 316, 314, 313, 312], icon: <Icons.Layers className="w-3.5 h-3.5" /> },
]

interface StatsGridProps { items?: StatItem[] }

export function StatsGrid({ items = defaultStats }: StatsGridProps) {
  return (
    <div className="grid grid-cols-4 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden">
      {items.map((s, i) => (
        <div key={i} className="pt-[16px] px-[18px] pb-[18px] border-r border-[var(--border-faint)] flex flex-col gap-[6px] relative last:border-r-0">
          <span className="text-[12px] text-[var(--text-mute)] flex items-center gap-[7px]">
            {s.icon}
            <span>{s.label}</span>
          </span>
          <span className="text-[26px] font-medium tracking-tight text-[var(--text)] mt-[2px]">
            {s.value}
            {s.unit && <span className="text-[14px] text-[var(--text-faint)] ml-[3px]">{s.unit}</span>}
          </span>
          <span className={cn(
            "font-mono text-[11px] inline-flex items-center gap-[4px]",
            s.deltaDir === "up" && "text-emerald-500",
            s.deltaDir === "down" && "text-red-500",
            s.deltaDir === "flat" && "text-gray-500"
          )}>
            {s.deltaDir === 'up' ? '↑' : s.deltaDir === 'down' ? '↓' : '—'} {s.delta}
          </span>
          <Sparkline
            data={s.spark}
            color={s.deltaDir === 'down' ? '#ef4444' : '#10b981'}
            className="absolute right-[14px] top-[14px] w-[70px] h-[28px] opacity-[0.85]"
          />
        </div>
      ))}
    </div>
  )
}
