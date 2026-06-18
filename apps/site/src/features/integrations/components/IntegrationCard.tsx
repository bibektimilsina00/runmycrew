import { ArrowUpRight } from 'lucide-react'
import type { Integration } from '../data/integrations'

/**
 * Square-ish integration tile — letter swatch + name + category + a
 * one-line description. Outlined card, accent border on hover.
 */
export function IntegrationCard({ i }: { i: Integration }) {
  return (
    <div className="group flex h-full flex-col gap-3.5 rounded-[12px] border border-border bg-card/40 p-5 transition-colors hover:border-foreground/25 hover:bg-card">
      <div className="flex items-start justify-between">
        <span
          className="grid h-[38px] w-[38px] place-items-center rounded-[9px] font-mono text-[12.5px] font-bold text-white"
          style={{ background: i.color }}
        >
          {i.letter}
        </span>
        <ArrowUpRight
          className="h-4 w-4 text-muted-foreground transition-colors group-hover:text-foreground"
          strokeWidth={1.8}
        />
      </div>
      <div className="flex flex-col gap-1">
        <div className="text-[14.5px] font-semibold text-foreground">{i.name}</div>
        <div className="text-[11.5px] font-medium uppercase tracking-[0.07em] text-muted-foreground/70">
          {i.category}
        </div>
      </div>
      <div className="text-[13px] leading-snug text-muted-foreground">
        {i.description}
      </div>
    </div>
  )
}
