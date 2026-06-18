import { Check, Minus } from 'lucide-react'
import { COMPARISON } from '../data/tiers'

/**
 * Stripe-style comparison matrix. Sticky tier header row + grouped
 * row sections. Booleans render as check / dash; strings render
 * verbatim.
 */
export function PricingComparison() {
  return (
    <div className="overflow-hidden rounded-[12px] border border-border">
      <div className="grid grid-cols-[1.4fr_1fr_1fr_1fr] border-b border-border bg-card/40">
        <div className="px-5 py-4 text-[13px] font-semibold text-muted-foreground">
          Compare plans
        </div>
        {(['Free', 'Pro', 'Enterprise'] as const).map((name) => (
          <div key={name} className="border-l border-border px-5 py-4 text-center">
            <div className="text-[14px] font-semibold text-foreground">{name}</div>
          </div>
        ))}
      </div>

      {COMPARISON.map((g) => (
        <div key={g.group}>
          <div className="border-b border-border bg-card/20 px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
            {g.group}
          </div>
          {g.rows.map((r) => (
            <div
              key={r.label}
              className="grid grid-cols-[1.4fr_1fr_1fr_1fr] border-b border-border last:border-b-0"
            >
              <div className="px-5 py-3 text-[13.5px] text-foreground/85">{r.label}</div>
              <Cell value={r.free} />
              <Cell value={r.pro} />
              <Cell value={r.enterprise} />
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

function Cell({ value }: { value: string | boolean }) {
  return (
    <div className="flex items-center justify-center border-l border-border px-5 py-3 text-center text-[13px] text-foreground/85">
      {typeof value === 'boolean' ? (
        value ? (
          <Check className="h-[16px] w-[16px] text-primary" strokeWidth={2.4} />
        ) : (
          <Minus className="h-[14px] w-[14px] text-muted-foreground/40" strokeWidth={2} />
        )
      ) : (
        <span>{value}</span>
      )}
    </div>
  )
}
