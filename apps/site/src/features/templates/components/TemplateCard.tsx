import Link from 'next/link'
import { Workflow } from 'lucide-react'
import type { Template } from '../data/templates'

/**
 * Ports the product app's "inspo-card" template tile to the site:
 *
 *   ┌──────────────────────────────┐
 *   │ idx                          │   <- gradient art region (4:3)
 *   │                              │
 *   │   ┌────────────────────┐    │
 *   │   │  ▔▔▔▔▔ window bar  │    │   <- offset mock preview that
 *   │   │                    │    │      bleeds off the bottom
 *   │   │                    │    │
 *   │   └────────────────────┘    │
 *   │  [LABEL]                     │
 *   ├──────────────────────────────┤
 *   │ Title                        │
 *   │ ⚯ Kind          N steps      │
 *   └──────────────────────────────┘
 *
 * Site typography (Inter + JetBrains Mono via the global font-features
 * map) is layered on top — the geometry comes from the product app,
 * the text style stays consistent with the marketing site.
 */
export function TemplateCard({ t, idx }: { t: Template; idx: number }) {
  return (
    <Link
      href={`/templates/${t.slug}`}
      className="group relative flex h-full flex-col overflow-hidden rounded-[12px] border border-border bg-card/30 transition-[transform,border-color] duration-200 hover:-translate-y-[2px] hover:border-foreground/30"
    >
      {/* Art region — 4:3, gradient bg with offset window mock */}
      <div
        className="relative aspect-[4/3] overflow-hidden"
        style={{ background: ART_GRADIENTS[idx % ART_GRADIENTS.length] }}
      >
        {/* Index marker top-left */}
        <span className="absolute left-3 top-2.5 font-mono text-[10px] tracking-[0.12em] text-foreground/55">
          {String(idx + 1).padStart(2, '0')}
        </span>

        {/* Inset mock window — offset from the product app, animated on
            hover: rises ~6px, scales 1.025, with a soft accent halo. */}
        <div
          className="absolute bottom-[-10%] left-[12%] flex h-[80%] w-[76%] origin-bottom flex-col overflow-hidden rounded-t-[10px] border border-white/[0.12] bg-[#08090a] shadow-[0_18px_40px_-20px_rgba(0,0,0,0.6)] transition-[transform,box-shadow,border-color] duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:-translate-y-[6px] group-hover:scale-[1.025] group-hover:border-white/[0.18] group-hover:shadow-[0_28px_60px_-22px_rgba(0,0,0,0.75)]"
        >
          <div className="h-[12px] border-b border-white/[0.06] bg-white/[0.04]" />
          <div
            className="flex-1 transition-opacity duration-700 group-hover:opacity-90"
            style={{
              backgroundImage:
                'linear-gradient(135deg, rgba(255,255,255,0.06) 25%, transparent 25%)',
              backgroundSize: '10px 10px',
              backgroundColor: 'rgba(255,255,255,0.025)',
            }}
          />
        </div>

        {/* Category label bottom-left */}
        <span className="absolute bottom-2.5 left-3 inline-flex items-center rounded-[5px] bg-black/55 px-2 py-[3px] font-mono text-[10px] uppercase tracking-[0.08em] text-foreground backdrop-blur-md">
          {t.category}
        </span>
      </div>

      {/* Meta footer */}
      <div className="flex flex-col gap-[7px] border-t border-border bg-card/60 px-[14px] py-[12px]">
        <div className="text-[13.5px] font-medium leading-snug tracking-[-0.01em] text-foreground">
          {t.title}
        </div>
        <div className="flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.08em] text-muted-foreground/85">
          <span className="inline-flex items-center gap-1.5">
            <Workflow className="h-[11px] w-[11px]" strokeWidth={1.8} /> {t.category}
          </span>
          <span>{t.steps.length} steps</span>
        </div>
      </div>
    </Link>
  )
}

/* Three gradients — two bluish + one green. Cycle by card index so
   the grid reads as a single surface with subtle hue variation. */
const ART_GRADIENTS = [
  // Indigo
  'radial-gradient(ellipse at 70% 30%, rgba(94,106,210,0.55), rgba(20,28,52,0.55) 60%), #0c0d18',
  // Cyan
  'radial-gradient(ellipse at 30% 60%, rgba(77,170,254,0.55), rgba(15,30,52,0.55) 65%), #0a1320',
  // Emerald
  'radial-gradient(ellipse at 50% 70%, rgba(63,185,138,0.55), rgba(18,40,30,0.55) 65%), #0a1410',
]
