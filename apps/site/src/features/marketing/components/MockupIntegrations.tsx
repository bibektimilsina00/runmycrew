'use client'

import { useState } from 'react'
import { Plug } from 'lucide-react'
import { INTEGRATIONS } from '../data/site'

/**
 * Connect-section mockup — 3-column integration grid with click-to-toggle
 * connect buttons. The counter in the header tracks the live state so
 * users feel the surface respond.
 */
export function MockupIntegrations() {
  const [connected, setConnected] = useState<Record<string, boolean>>(
    Object.fromEntries(INTEGRATIONS.map((i) => [i.key, i.defaultConnected])),
  )

  const total = Object.values(connected).filter(Boolean).length

  return (
    <div className="overflow-hidden rounded-[13px] border border-white/[0.09] bg-[#0c0d0f] shadow-[0_40px_100px_-40px_rgba(0,0,0,0.8)]">
      <div className="flex items-center gap-2.5 border-b border-white/[0.06] px-[18px] py-3.5">
        <Plug className="h-[15px] w-[15px] text-muted-foreground" strokeWidth={1.8} />
        <span className="text-[13.5px] font-semibold">Integrations</span>
        <span className="ml-auto rounded-[5px] bg-[#4cc38a]/15 px-2 py-[2px] text-[11px] font-semibold text-[#4cc38a]">
          {total} connected
        </span>
      </div>

      <div className="grid grid-cols-1 gap-px bg-white/[0.06] sm:grid-cols-2 lg:grid-cols-3">
        {INTEGRATIONS.map((c) => {
          const on = connected[c.key]
          return (
            <div key={c.key} className="flex flex-col gap-[13px] bg-[#0c0d0f] px-[18px] py-5">
              <div className="flex items-center gap-3">
                <span
                  className="grid h-[34px] w-[34px] shrink-0 place-items-center rounded-[9px] font-mono text-[13px] font-bold text-white"
                  style={{ background: c.bg }}
                >
                  {c.letter}
                </span>
                <span className="flex min-w-0 flex-col leading-[1.3]">
                  <span className="text-[14px] font-medium text-foreground">{c.name}</span>
                  <span className="text-[11.5px] text-muted-foreground/80">{c.sub}</span>
                </span>
              </div>
              <button
                onClick={() => setConnected((s) => ({ ...s, [c.key]: !s[c.key] }))}
                className={`flex w-full items-center justify-center gap-1.5 rounded-lg border px-2 py-2 text-[12.5px] font-semibold transition-[filter] hover:brightness-110 ${
                  on
                    ? 'border-[#4cc38a]/30 bg-[#4cc38a]/12 text-[#4cc38a]'
                    : 'border-white/10 bg-white/[0.04] text-foreground/80'
                }`}
              >
                {on ? 'Connected' : 'Connect'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
