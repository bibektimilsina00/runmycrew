'use client'

import { useState } from 'react'
import { Check } from 'lucide-react'
import { BrandGlyph } from './BrandGlyph'
import { RUN_DETAIL_TITLE, RUN_DETAIL_TOTAL, RUN_STEPS } from '../data/site'

/**
 * Observe-section mockup — split pane with a step list on the left and a
 * payload preview on the right. Clicking a step swaps the payload, which
 * is the core "inspect any step" interaction the design highlights.
 */
export function MockupObserve() {
  const [idx, setIdx] = useState(0)
  const active = RUN_STEPS[idx]

  return (
    <div className="grid grid-cols-1 overflow-hidden rounded-[13px] border border-white/[0.09] bg-[#0c0d0f] shadow-[0_40px_100px_-40px_rgba(0,0,0,0.8)] md:grid-cols-[1.1fr_1fr]">
      {/* Steps */}
      <div className="md:border-r md:border-white/[0.06]">
        <div className="flex items-center gap-2.5 border-b border-white/[0.06] px-[18px] py-3.5">
          <span className="h-2 w-2 rounded-full bg-[#4cc38a] shadow-[0_0_0_3px_rgba(76,195,138,0.18)]" />
          <span className="text-[13.5px] font-semibold">{RUN_DETAIL_TITLE}</span>
          <span className="ml-auto font-mono text-[11px] text-[#4cc38a]">{RUN_DETAIL_TOTAL}</span>
        </div>
        <div className="px-3 py-2">
          {RUN_STEPS.map((s, i) => {
            const on = i === idx
            return (
              <button
                key={s.title}
                onClick={() => setIdx(i)}
                className={`mb-0.5 flex w-full items-center gap-2.5 rounded-lg px-3 py-[11px] text-left transition-colors hover:bg-white/[0.04] ${
                  on ? 'bg-white/[0.05]' : ''
                }`}
              >
                <span
                  className="grid h-[22px] w-[22px] shrink-0 place-items-center rounded-md font-mono text-[10px] font-bold text-white"
                  style={{ background: s.iconBg }}
                >
                  <BrandGlyph slug={s.slug} fallback={s.icon} size={13} />
                </span>
                <span className="flex-1 text-[13px] font-medium text-foreground/85">{s.title}</span>
                <span className="font-mono text-[11px] text-muted-foreground/70">{s.ms}</span>
                <Check className="h-3.5 w-3.5 text-[#4cc38a]" strokeWidth={2.4} />
              </button>
            )
          })}
        </div>
      </div>

      {/* Payload */}
      <div className="flex flex-col bg-[#0a0b0c]">
        <div className="border-b border-white/[0.06] px-[18px] py-3.5 text-[12px] font-semibold uppercase tracking-[0.04em] text-muted-foreground">
          {active.title} · Payload
        </div>
        <pre className="m-0 overflow-hidden whitespace-pre-wrap px-[18px] py-[18px] font-mono text-[12px] leading-[1.7] text-muted-foreground">
          {active.payload}
        </pre>
      </div>
    </div>
  )
}
