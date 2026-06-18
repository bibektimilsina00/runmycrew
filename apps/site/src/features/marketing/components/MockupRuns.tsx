import { Activity } from 'lucide-react'
import { RUNS } from '../data/site'

/**
 * Run-section mockup — recent runs list. Each row carries a glow-ringed
 * status dot, name, trigger pill, duration and time. Pure data render
 * (no state) — keeps the bundle small and the layout predictable.
 */
export function MockupRuns() {
  return (
    <div className="overflow-hidden rounded-[13px] border border-white/[0.09] bg-[#0c0d0f] shadow-[0_40px_100px_-40px_rgba(0,0,0,0.8)]">
      <div className="flex items-center gap-2.5 border-b border-white/[0.06] px-[18px] py-3.5">
        <Activity className="h-[15px] w-[15px] text-muted-foreground" strokeWidth={1.8} />
        <span className="text-[13.5px] font-semibold">Recent runs</span>
        <span className="ml-auto rounded-[5px] bg-white/[0.05] px-2 py-[2px] font-mono text-[11px] text-muted-foreground/80">
          214 today
        </span>
      </div>
      <div>
        {RUNS.map((r) => (
          <div
            key={r.name}
            className="flex items-center gap-3.5 border-b border-white/[0.04] px-[18px] py-3.5 transition-colors last:border-b-0 hover:bg-white/[0.02]"
          >
            <span
              className="h-2 w-2 shrink-0 rounded-full"
              style={{ background: r.dot, boxShadow: `0 0 0 3px ${r.glow}` }}
            />
            <span className="flex-1 truncate text-[13.5px] font-medium text-foreground/85">
              {r.name}
            </span>
            <span className="rounded-[5px] border border-white/[0.06] bg-white/[0.04] px-2 py-[2px] font-mono text-[11.5px] text-muted-foreground">
              {r.trigger}
            </span>
            <span className="w-12 text-right font-mono text-[11.5px] text-muted-foreground/70">
              {r.dur}
            </span>
            <span className="w-[50px] text-right text-[11.5px] text-muted-foreground/60">
              {r.time}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
