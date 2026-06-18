import Link from 'next/link'
import { Check } from 'lucide-react'
import type { Tier } from '../data/tiers'

export function PricingTier({ tier }: { tier: Tier }) {
  return (
    <div
      className={`relative flex flex-col gap-6 rounded-[14px] border p-7 transition-colors ${
        tier.highlight
          ? 'border-primary/50 bg-card/60 shadow-[0_30px_80px_-40px_color-mix(in_oklab,var(--primary)_40%,transparent)]'
          : 'border-border bg-card/30'
      }`}
    >
      {tier.highlight && (
        <span className="absolute right-5 top-5 inline-flex items-center rounded-full bg-primary/20 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-[0.07em] text-primary">
          Most popular
        </span>
      )}

      <div className="flex flex-col gap-2">
        <div className="text-[17px] font-semibold text-foreground">{tier.name}</div>
        <div className="text-[13px] leading-snug text-muted-foreground">{tier.tagline}</div>
      </div>

      <div className="flex items-baseline gap-1">
        <span className="font-mono text-[34px] font-semibold tracking-[-0.022em] text-foreground">
          {tier.price}
        </span>
        {tier.cadence && (
          <span className="text-[13px] font-medium text-muted-foreground">{tier.cadence}</span>
        )}
      </div>

      <Link
        href={tier.ctaHref}
        className={`inline-flex h-[36px] items-center justify-center gap-[7px] rounded-[8px] px-[16px] text-[13px] font-semibold transition-[filter,colors] ${
          tier.highlight
            ? 'bg-primary text-primary-foreground hover:brightness-110'
            : 'border border-border bg-white/[0.02] text-foreground/90 hover:bg-white/[0.06]'
        }`}
      >
        {tier.ctaLabel}
      </Link>

      <ul className="flex flex-col gap-2.5">
        {tier.features.map((f) => (
          <li key={f} className="flex items-start gap-2 text-[13.5px] leading-snug text-foreground/85">
            <Check className="mt-[3px] h-[14px] w-[14px] shrink-0 text-primary" strokeWidth={2.4} />
            <span>{f}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
