'use client'

import { useState } from 'react'
import { BrandMark } from './BrandMark'
import { BrandGlyph } from './BrandGlyph'
import { EXAMPLES } from '../data/site'

/**
 * Build-section mockup — header w/ active example label, body shows the
 * workflow's nodes stacked vertically with a connector between each.
 * Local state (active example index) is independent from the hero so the
 * two sections can show different examples at once.
 */
export function MockupWorkflow() {
  const [idx] = useState(0) // single-example surface; kept stateful for parity
  const ex = EXAMPLES[idx]

  return (
    <div className="overflow-hidden rounded-[13px] border border-white/[0.09] bg-[#0c0d0f] shadow-[0_40px_100px_-40px_rgba(0,0,0,0.8)]">
      <div className="flex items-center gap-2.5 border-b border-white/[0.06] px-[18px] py-3.5">
        <span className="grid h-[22px] w-[22px] place-items-center rounded-md bg-primary/15 text-primary">
          <BrandMark className="h-[13px] w-[13px]" />
        </span>
        <span className="text-[13.5px] font-semibold">{ex.label}</span>
        <span className="ml-auto rounded-[5px] bg-white/[0.05] px-2 py-[2px] font-mono text-[11px] text-muted-foreground/80">
          {ex.nodes.length} steps
        </span>
      </div>
      <div
        className="px-[26px] py-[30px]"
        style={{
          backgroundImage: 'radial-gradient(rgba(255,255,255,0.045) 1px,transparent 1px)',
          backgroundSize: '20px 20px',
        }}
      >
        {ex.nodes.map((n, i) => (
          <div key={i}>
            <div className="flex items-center gap-3.5">
              <span className="w-[62px] shrink-0 font-mono text-[10px] font-semibold tracking-[0.07em] text-muted-foreground/70">
                {n.kind}
              </span>
              <div
                className={`flex max-w-[440px] flex-1 items-center gap-3 rounded-[11px] border px-[15px] py-[13px] ${
                  n.kind === 'TRIGGER'
                    ? 'border-primary bg-primary/15'
                    : 'border-white/[0.09] bg-white/[0.02]'
                }`}
              >
                <span
                  className="grid h-[30px] w-[30px] shrink-0 place-items-center rounded-lg font-mono text-[11px] font-bold text-white"
                  style={{ background: n.iconBg }}
                >
                  <BrandGlyph slug={n.slug} fallback={n.icon} size={16} />
                </span>
                <span className="flex min-w-0 flex-col leading-[1.3]">
                  <span className="text-[14px] font-medium text-foreground">{n.title}</span>
                  <span className="text-[12px] text-muted-foreground/80">{n.sub}</span>
                </span>
              </div>
            </div>
            {!n.last && (
              <div className="ml-[93px] h-[22px] w-px bg-white/[0.14]" />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
