'use client'

import Link from 'next/link'
import { Bot, Cog, Plug, Server, Shield, Sparkles } from 'lucide-react'
import {
  NAV_MENU_BLOG,
  NAV_MENU_DOCS,
  type NavHeroCard,
  type NavMenuKey,
  type NavMiniCard,
  type NavThumbCard,
} from '../data/site'

const ICONS = {
  sparkles: Sparkles,
  plug:     Plug,
  server:   Server,
  shield:   Shield,
  bot:      Bot,
  cog:      Cog,
} as const

interface NavMenuProps {
  which: NavMenuKey
  /** Mouse re-enters keep the menu open; leaving fires close. */
  onMouseEnter: () => void
  onMouseLeave: () => void
}

/**
 * Mega-menu popup shown when the user hovers Docs or Blog in the nav.
 * Two layouts share a 720px shell:
 *
 *   docs → 2 hero cards (each a labelled product mockup) on top, 3
 *          icon-led mini-cards underneath.
 *   blog → 1 large featured card + 1 enterprise card on top, 3
 *          thumb cards underneath.
 *
 * The shell is positioned absolute by the parent (`MarketingNav`); this
 * component owns layout + hover-leave plumbing only.
 */
export function NavMenu({ which, onMouseEnter, onMouseLeave }: NavMenuProps) {
  return (
    <div
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className="w-[720px] rounded-[14px] border border-white/[0.1] bg-[#0f1011] p-3 shadow-[0_30px_80px_-20px_rgba(0,0,0,0.8)]"
    >
      {which === 'docs' ? <DocsMenu /> : <BlogMenu />}
    </div>
  )
}

/* ─── Docs ─────────────────────────────────────────────────────────── */

function DocsMenu() {
  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 gap-3">
        {NAV_MENU_DOCS.hero.map((c) => (
          <HeroCard key={c.title} card={c} />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-3">
        {NAV_MENU_DOCS.mini.map((c) => (
          <MiniCard key={c.title} card={c} />
        ))}
      </div>
    </div>
  )
}

function HeroCard({ card }: { card: NavHeroCard }) {
  return (
    <Link
      href={card.href}
      className="group overflow-hidden rounded-[10px] border border-white/[0.07] bg-white/[0.02] transition-colors hover:border-white/[0.14] hover:bg-white/[0.05]"
    >
      <div className="h-[120px] overflow-hidden bg-[#08090a]">
        <HeroVisual which={card.visual} />
      </div>
      <div className="px-3.5 py-3 text-[13.5px] font-semibold text-foreground">
        {card.title}
      </div>
    </Link>
  )
}

function MiniCard({ card }: { card: NavMiniCard }) {
  const Icon = ICONS[card.icon]
  return (
    <Link
      href={card.href}
      className="group flex flex-col gap-1 rounded-[10px] border border-white/[0.07] bg-white/[0.02] px-3.5 py-3 transition-colors hover:border-white/[0.14] hover:bg-white/[0.05]"
    >
      <div className="flex items-center gap-2 text-foreground">
        <Icon className="h-[14px] w-[14px] text-muted-foreground" strokeWidth={1.8} />
        <span className="text-[13.5px] font-semibold">{card.title}</span>
      </div>
      <div className="text-[12px] text-muted-foreground">{card.sub}</div>
    </Link>
  )
}

/* ─── Blog ─────────────────────────────────────────────────────────── */

function BlogMenu() {
  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-[1.4fr_1fr] gap-3">
        <FeaturedCard />
        <EnterpriseCard />
      </div>
      <div className="grid grid-cols-3 gap-3">
        {NAV_MENU_BLOG.thumbs.map((c) => (
          <ThumbCard key={c.title} card={c} />
        ))}
      </div>
    </div>
  )
}

function FeaturedCard() {
  return (
    <Link
      href={NAV_MENU_BLOG.featured.href}
      className="group overflow-hidden rounded-[10px] border border-white/[0.07] bg-white/[0.02] transition-colors hover:border-white/[0.14] hover:bg-white/[0.05]"
    >
      <div className="h-[180px] overflow-hidden bg-[#08090a]">
        <FeaturedVisual />
      </div>
      <div className="px-3.5 py-3 text-[14px] font-semibold text-foreground">
        {NAV_MENU_BLOG.featured.title}
      </div>
    </Link>
  )
}

function EnterpriseCard() {
  return (
    <Link
      href={NAV_MENU_BLOG.enterprise.href}
      className="group flex h-full flex-col gap-2 overflow-hidden rounded-[10px] border border-white/[0.07] bg-white/[0.02] px-3.5 py-3 transition-colors hover:border-white/[0.14] hover:bg-white/[0.05]"
    >
      <span className="inline-flex w-fit items-center gap-1.5 rounded-[5px] bg-[#e5b341]/15 px-2 py-[2px] text-[10px] font-semibold uppercase tracking-[0.07em] text-[#e5b341]">
        <span className="h-1 w-1 rounded-full bg-[#e5b341]" />
        Enterprise
      </span>
      <span className="text-[14px] font-semibold leading-snug text-foreground">
        Enterprise features for fast, scalable workflows
      </span>
      <div className="mt-auto">
        <RainbowBar />
        <div className="mt-2 text-[12.5px] font-medium text-foreground/85">
          {NAV_MENU_BLOG.enterprise.title}
        </div>
      </div>
    </Link>
  )
}

function ThumbCard({ card }: { card: NavThumbCard }) {
  return (
    <Link
      href={card.href}
      className="group overflow-hidden rounded-[10px] border border-white/[0.07] bg-white/[0.02] transition-colors hover:border-white/[0.14] hover:bg-white/[0.05]"
    >
      <div className="h-[100px] overflow-hidden bg-[#08090a]">
        <ThumbVisual which={card.visual} />
      </div>
      <div className="px-3 py-2.5 text-[12.5px] font-medium text-foreground/90">
        {card.title}
      </div>
    </Link>
  )
}

/* ─── Visuals (pure SVG / gradient placeholders) ───────────────────── */

function HeroVisual({ which }: { which: NavHeroCard['visual'] }) {
  if (which === 'workflow') return <WorkflowVisual />
  if (which === 'chart')    return <ChartVisual />
  return <LogsVisual />
}

function WorkflowVisual() {
  return (
    <svg viewBox="0 0 320 120" className="h-full w-full">
      <defs>
        <linearGradient id="nv-grad-a" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%"   stopColor="#5e6ad2" />
          <stop offset="100%" stopColor="#7aa2f7" />
        </linearGradient>
        <linearGradient id="nv-grad-b" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%"   stopColor="#4cc38a" />
          <stop offset="100%" stopColor="#7ee0a9" />
        </linearGradient>
      </defs>
      <g opacity="0.95">
        <rect x="40"  y="20" width="170" height="14" rx="3" fill="#e5675f"  />
        <rect x="40"  y="40" width="120" height="14" rx="3" fill="url(#nv-grad-a)" />
        <rect x="40"  y="60" width="150" height="14" rx="3" fill="url(#nv-grad-b)" />
      </g>
      <g stroke="rgba(255,255,255,0.18)" strokeWidth="0.6" fill="none">
        <rect x="35"  y="14" width="200" height="74" rx="6" />
        <path d="M232 50 H280" />
        <rect x="278" y="42" width="22" height="16" rx="3" />
      </g>
    </svg>
  )
}

function ChartVisual() {
  const bars = [22, 38, 30, 56, 44, 70, 50]
  return (
    <svg viewBox="0 0 320 120" className="h-full w-full">
      <g transform="translate(40,30)">
        <rect x="-6" y="-12" width="244" height="80" rx="6" fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.1)" strokeWidth="0.6" />
        {bars.map((h, i) => (
          <rect
            key={i}
            x={4 + i * 32}
            y={70 - h}
            width="18"
            height={h}
            rx="3"
            fill={i % 2 ? '#5e6ad2' : '#4cc38a'}
            opacity={0.8}
          />
        ))}
      </g>
    </svg>
  )
}

function LogsVisual() {
  return (
    <svg viewBox="0 0 320 120" className="h-full w-full">
      <rect x="40" y="20" width="240" height="80" rx="6" fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.1)" strokeWidth="0.6" />
      {[0, 1, 2, 3, 4].map((i) => (
        <g key={i} transform={`translate(56,${34 + i * 12})`}>
          <circle cx="0" cy="0" r="2.5" fill="#4cc38a" />
          <rect x="10" y="-3" width={140 - i * 18} height="6" rx="2" fill="rgba(255,255,255,0.1)" />
          <rect x="180" y="-3" width="22" height="6" rx="2" fill="rgba(255,255,255,0.06)" />
        </g>
      ))}
    </svg>
  )
}

function FeaturedVisual() {
  return (
    <svg viewBox="0 0 460 180" className="h-full w-full">
      <defs>
        <linearGradient id="nv-feat" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%"   stopColor="#5e6ad2" />
          <stop offset="50%"  stopColor="#7e69d6" />
          <stop offset="100%" stopColor="#08090a" />
        </linearGradient>
      </defs>
      <rect width="460" height="180" fill="url(#nv-feat)" />
      {/* Sparse star field */}
      <g fill="#fff" opacity="0.55">
        {Array.from({ length: 28 }).map((_, i) => (
          <circle
            key={i}
            cx={(i * 47) % 460}
            cy={(i * 31) % 180}
            r={i % 3 === 0 ? 1.4 : 0.8}
          />
        ))}
      </g>
      {/* Fuse mark front */}
      <g transform="translate(200,55)">
        <rect x="0"  y="0"  width="34" height="34" rx="10" fill="#fff" opacity="0.45" />
        <rect x="14" y="14" width="34" height="34" rx="10" fill="#fff" />
      </g>
    </svg>
  )
}

function RainbowBar() {
  return (
    <div className="h-[3px] w-full overflow-hidden rounded-full">
      <div className="h-full w-full bg-[linear-gradient(90deg,#5e6ad2_0%,#7aa2f7_25%,#4cc38a_50%,#e5b341_75%,#e5675f_100%)]" />
    </div>
  )
}

function ThumbVisual({ which }: { which: NavThumbCard['visual'] }) {
  if (which === 'series')   return <SeriesVisual />
  if (which === 'collab')   return <CollabVisual />
  return <GraphVisual />
}

function SeriesVisual() {
  return (
    <svg viewBox="0 0 220 100" className="h-full w-full">
      <rect width="220" height="100" fill="#0a0b0c" />
      <g transform="translate(20,16)" fill="#fff">
        <rect width="14" height="14" rx="3.5" opacity="0.45" />
        <rect x="8" y="8" width="14" height="14" rx="3.5" />
      </g>
      <text x="56" y="32" fontSize="11" fontFamily="JetBrains Mono, monospace" fill="rgba(255,255,255,0.7)">$8M · Seed</text>
      <g transform="translate(20,52)">
        <rect width="180" height="28" rx="4" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.1)" strokeWidth="0.6" />
        <text x="14" y="18" fontSize="10" fill="rgba(255,255,255,0.65)" fontFamily="Inter, sans-serif">Standard · SV Angel · Sequoia</text>
      </g>
    </svg>
  )
}

function CollabVisual() {
  return (
    <svg viewBox="0 0 220 100" className="h-full w-full">
      <rect width="220" height="100" fill="#0a0b0c" />
      <g>
        <circle cx="60"  cy="40" r="14" fill="#5e6ad2" opacity="0.85" />
        <circle cx="110" cy="55" r="10" fill="#4cc38a" opacity="0.85" />
        <circle cx="150" cy="32" r="11" fill="#e5b341" opacity="0.85" />
        <circle cx="170" cy="62" r="9"  fill="#e5675f" opacity="0.85" />
      </g>
      <g stroke="rgba(255,255,255,0.18)" strokeWidth="0.6" fill="none">
        <path d="M60 40 L110 55 L150 32 L170 62" />
      </g>
    </svg>
  )
}

function GraphVisual() {
  return (
    <svg viewBox="0 0 220 100" className="h-full w-full">
      <rect width="220" height="100" fill="#0a0b0c" />
      <g stroke="rgba(255,255,255,0.16)" strokeWidth="0.5" fill="none">
        {Array.from({ length: 8 }).map((_, i) => (
          <line key={i} x1={20 + i * 24} y1="14" x2={20 + i * 24} y2="86" />
        ))}
        {Array.from({ length: 5 }).map((_, i) => (
          <line key={i} x1="14" y1={18 + i * 18} x2="206" y2={18 + i * 18} />
        ))}
      </g>
      <g fill="#5e6ad2" opacity="0.85">
        {[1, 3, 4, 6].map((c, i) => (
          <rect key={i} x={20 + c * 24 - 7} y={18 + i * 18 - 5} width="14" height="10" rx="2" />
        ))}
      </g>
    </svg>
  )
}
