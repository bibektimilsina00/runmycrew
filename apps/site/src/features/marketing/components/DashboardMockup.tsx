'use client'


import {
  ChevronsUpDown,
  Search,
  ArrowRight,
  Plug,
  Plus,
  Bot,
  ChevronDown,
  ArrowUpRight,
} from 'lucide-react'
import { FuseMark } from './FuseMark'
import {
  EXAMPLES,
  HERO_METRICS,
  HERO_SIDE_CONN,
  HERO_SIDE_TOP,
  HERO_SUGGESTIONS,
} from '../data/site'

/**
 * Hero product shot — stylised but fully-populated recreation of the
 * Fuse dashboard. Matches the production layout (apps/web) panel-for-
 * panel: greeting row with Connect-app / New-automation buttons, four
 * stat cards with mono-numerals + sparklines + deltas, the Build-with-
 * Fuse-AI prompt card (interactive — click a prompt chip to swap the
 * textarea text), and a Recent runs strip below it.
 *
 * The mockup is fixed-height (620px) with the dashboard body scrolling
 * internally so the lower panels read as "there's more if you scroll"
 * the same way the real product does on a 720p screen.
 */
export function DashboardMockup() {
  const active = EXAMPLES[0]

  return (
    <div className="relative mt-12 sm:mt-16">
      {/* Soft accent glow behind the card */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-[-160px] h-[420px] w-[1080px] -translate-x-1/2 bg-[radial-gradient(ellipse_at_center,color-mix(in_oklab,var(--primary)_18%,transparent),transparent_68%)] blur-2xl"
      />

      <div className="relative flex h-[620px] overflow-hidden rounded-[14px] border border-white/10 bg-[#0c0d0f] shadow-[0_60px_160px_-40px_rgba(0,0,0,0.92),0_0_0_1px_rgba(255,255,255,0.02)]">
        <Sidebar />

        {/* ── Main ────────────────────────────────────────────── */}
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar />

          <div className="flex-1 overflow-hidden">
            <div className="h-full overflow-hidden px-[26px] py-6">
              {/* Greeting + status + actions */}
              <div className="mb-3.5 flex items-center gap-2">
                <span className="h-[7px] w-[7px] animate-[fusePulse_2.4s_ease-in-out_infinite] rounded-full bg-[#4cc38a]" />
                <span className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/80">
                  All systems operational
                </span>
                <span className="text-muted-foreground/40">·</span>
                <span className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/60">
                  Wed, Jun 18
                </span>
              </div>

              <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
                <div className="text-[24px] font-semibold tracking-[-0.02em] text-foreground">
                  Good evening, Bibek
                </div>
                <div className="flex items-center gap-2">
                  <button className="inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-white/[0.02] px-2.5 py-1.5 text-[11.5px] font-medium text-foreground/85 transition-colors hover:bg-white/[0.06]">
                    <Plug className="h-3 w-3" strokeWidth={1.8} />
                    Connect app
                  </button>
                  <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1.5 text-[11.5px] font-semibold text-primary-foreground transition-[filter] hover:brightness-110">
                    <Plus className="h-3 w-3" strokeWidth={2.2} />
                    New automation
                  </button>
                </div>
              </div>

              {/* Stats grid */}
              <div className="mb-5 grid grid-cols-4 gap-3">
                {HERO_METRICS.map((m) => (
                  <div
                    key={m.label}
                    className="relative rounded-[10px] border border-white/[0.07] bg-white/[0.018] px-3.5 py-3"
                  >
                    <div className="mb-2 text-[11px] font-medium text-muted-foreground/80">
                      {m.label}
                    </div>
                    <div className="flex items-end justify-between">
                      <div className="font-mono text-[22px] font-semibold tracking-[-0.02em] text-foreground">
                        {m.value}
                      </div>
                      <svg viewBox="0 0 60 18" className="h-[18px] w-[58px] -mb-1">
                        <polyline
                          points={m.spark}
                          fill="none"
                          stroke={m.color}
                          strokeWidth="1.4"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          opacity="0.9"
                        />
                      </svg>
                    </div>
                    <div className="mt-1 text-[11px] font-semibold" style={{ color: m.color }}>
                      {m.delta}
                    </div>
                  </div>
                ))}
              </div>

              {/* Build-with-Fuse-AI prompt card */}
              <div className="overflow-hidden rounded-xl border border-white/10 bg-[#0f1011]">
                <div className="flex items-center gap-2.5 border-b border-white/[0.05] px-4 py-3">
                  <span className="grid h-[23px] w-[23px] place-items-center rounded-md bg-primary/15 text-primary">
                    <FuseMark className="h-[13px] w-[13px]" />
                  </span>
                  <span className="text-[13px] font-semibold">Build with Fuse AI</span>
                  <span className="ml-auto inline-flex items-center gap-1.5 rounded-md border border-white/[0.07] px-2 py-[3px] text-[11px] text-muted-foreground">
                    <span className="h-[5px] w-[5px] rounded-full bg-[#4cc38a]" />
                    Claude Sonnet
                    <ChevronDown className="h-3 w-3 text-muted-foreground/70" strokeWidth={1.8} />
                  </span>
                </div>
                <div className="px-4 pb-3.5 pt-4">
                  <div className="min-h-[42px] text-[14.5px] leading-[1.5] text-foreground/85">
                    {active.text}
                    <span className="ml-[2px] inline-block h-[15px] w-[7px] -translate-y-[2px] animate-[fuseBlink_1.1s_infinite] bg-primary align-middle" />
                  </div>
                  <div className="mt-3.5 flex items-center justify-end">
                    <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-[13px] py-[7px] text-[12.5px] font-semibold text-primary-foreground transition-[filter] hover:brightness-110">
                      Generate workflow
                      <ArrowRight className="h-[13px] w-[13px]" strokeWidth={2.4} />
                    </button>
                  </div>
                </div>
              </div>

              {/* SUGGESTED AUTOMATIONS — caps eyebrow + 3-card grid */}
              <div className="mt-7 mb-3 flex items-center gap-2">
                <span className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
                  Suggested automations
                </span>
                <span className="h-px flex-1 bg-white/[0.06]" />
              </div>

              <div className="grid grid-cols-3 gap-3">
                {HERO_SUGGESTIONS.map((s) => (
                  <button
                    key={s.icon}
                    className="group flex flex-col gap-3 rounded-[10px] border border-white/[0.07] bg-white/[0.015] px-3 py-3 text-left transition-colors hover:border-white/[0.12] hover:bg-white/[0.04]"
                  >
                    <div className="flex items-start justify-between">
                      <span
                        className="grid h-[26px] w-[26px] place-items-center rounded-[7px] font-mono text-[10px] font-bold text-white"
                        style={{ background: s.iconBg }}
                      >
                        {s.icon}
                      </span>
                      <ArrowUpRight
                        className="h-3.5 w-3.5 text-muted-foreground/50 transition-colors group-hover:text-muted-foreground"
                        strokeWidth={1.9}
                      />
                    </div>
                    <span className="text-[12px] font-medium leading-[1.35] text-foreground/90">
                      {s.title}
                    </span>
                  </button>
                ))}
              </div>

              <div className="h-6" />
            </div>
          </div>
        </div>
      </div>

      <div className="mt-3 font-mono text-[11px] tracking-[0.04em] text-muted-foreground/60">
        FIG 0.1 — FUSE DASHBOARD · CLICK A PROMPT TO TRY IT
      </div>
    </div>
  )
}

/* ─── Sidebar + Topbar ─────────────────────────────────────────────── */

function Sidebar() {
  return (
    <aside className="hidden w-[230px] shrink-0 flex-col border-r border-white/[0.06] bg-[#0a0b0c] md:flex">
      <div className="flex items-center gap-2 px-[13px] pb-3 pt-[14px]">
        <span className="grid h-6 w-6 place-items-center rounded-md bg-gradient-to-br from-[#3a3f4a] to-[#23262c] text-[12px] font-semibold">
          B
        </span>
        <span className="text-[13px] font-medium">Bibek&apos;s Workspace</span>
        <ChevronsUpDown className="ml-auto h-[13px] w-[13px] text-muted-foreground/60" />
      </div>

      <div className="px-[11px] pb-[9px]">
        <div className="flex items-center gap-2 rounded-lg border border-white/[0.05] bg-white/[0.03] px-[9px] py-1.5">
          <Search className="h-[13px] w-[13px] text-muted-foreground/60" />
          <span className="flex-1 text-[12.5px] text-muted-foreground/60">Search</span>
          <span className="rounded bg-white/[0.05] px-1.5 py-[1px] font-mono text-[10.5px] text-muted-foreground/60">
            ⌘K
          </span>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-[1px] overflow-hidden px-[11px] py-0.5">
        <SideHeading>WORKSPACE</SideHeading>
        {HERO_SIDE_TOP.map((s) => (
          <button
            key={s.label}
            className={`flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-left text-[13px] font-medium transition-colors hover:bg-white/[0.05] ${
              s.active ? 'bg-white/[0.05] text-foreground' : 'text-[#c7c9ce]'
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-sm" style={{ background: s.dot }} />
            <span className="flex-1">{s.label}</span>
            {s.count && (
              <span className="font-mono text-[11px] text-muted-foreground/60">{s.count}</span>
            )}
          </button>
        ))}
        <SideHeading className="mt-3.5">CONNECTIONS</SideHeading>
        {HERO_SIDE_CONN.map((s) => (
          <div
            key={s.label}
            className="flex items-center gap-[9px] rounded-md px-2 py-1.5 text-[13px] text-[#9ca0a8] transition-colors hover:bg-white/[0.05]"
          >
            <span
              className="grid h-[18px] w-[18px] place-items-center rounded-[5px] font-mono text-[9px] font-bold text-white"
              style={{ background: s.bg }}
            >
              {s.letter}
            </span>
            <span className="flex-1">{s.label}</span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#4cc38a]" />
          </div>
        ))}

        {/* Copilot pill at the bottom of the sidebar */}
        <div className="mt-auto pb-2 pt-3">
          <button className="flex w-full items-center gap-2.5 rounded-md border border-white/[0.06] bg-white/[0.03] px-2 py-2 text-left transition-colors hover:bg-white/[0.06]">
            <span className="grid h-5 w-5 place-items-center rounded-md bg-primary text-primary-foreground">
              <Bot className="h-3 w-3" strokeWidth={1.8} />
            </span>
            <span className="flex flex-col leading-tight">
              <span className="text-[12.5px] font-medium text-foreground">Copilot</span>
              <span className="text-[10.5px] text-muted-foreground/70">Ask, edit, fix</span>
            </span>
          </button>
        </div>
      </div>
    </aside>
  )
}

function Topbar() {
  return (
    <div className="flex h-12 shrink-0 items-center gap-2.5 border-b border-white/[0.06] px-[18px]">
      <span className="text-[13px] font-medium text-muted-foreground">Bibek&apos;s Workspace</span>
      <span className="text-[#3a3e44]">/</span>
      <span className="text-[13px] font-semibold">Dashboard</span>
      <span className="ml-auto grid h-[26px] w-[26px] place-items-center rounded-full bg-gradient-to-br from-[#3a3f4a] to-[#23262c] text-[11px] font-semibold">
        B
      </span>
    </div>
  )
}

function SideHeading({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`px-2 pb-1 pt-2 text-[10px] font-semibold tracking-[0.07em] text-muted-foreground/60 ${className ?? ''}`}
    >
      {children}
    </div>
  )
}
