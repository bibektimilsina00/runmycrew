import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Loader2, Search, X, Sparkles, TrendingUp, Clock, Award, Layers, ChevronLeft, ChevronRight,
} from 'lucide-react'
import { useRef } from 'react'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useTemplates, useTemplateCategories } from '../hooks/useTemplates'
import { TemplateCard } from '../components/TemplateCard'
import { cn } from '@/lib/cn'
import type { TemplateListItem, TemplateSort } from '../types/templatesTypes'

/**
 * Fresh Templates gallery — deliberately NOT an n8n clone.
 *
 * Visual language:
 * - A single sticky filter bar at the top of the scroll area — no
 *   sidebar. Everything sits in a 1180px column so line lengths stay
 *   comfortable.
 * - Every card has a real workflow preview (graph render) instead of
 *   an empty gradient. Reads more like Vercel deploy templates.
 * - Three surfaces (spotlight banner → horizontal-scroll row → grid)
 *   give the page rhythm without needing multiple category headers.
 * - Category chips live in the filter bar; when a chip is active the
 *   heading swaps to "3 Marketing templates" so the visitor never has
 *   to guess which slice they're looking at.
 */

const SORT_OPTIONS: { id: TemplateSort; label: string; icon: React.ElementType }[] = [
  { id: 'popular', label: 'Popular', icon: TrendingUp },
  { id: 'newest', label: 'Recent', icon: Clock },
]

export function Templates() {
  const navigate = useNavigate()
  const [cat, setCat] = useState<string>('all')
  const [sort, setSort] = useState<TemplateSort>('popular')
  const [search, setSearch] = useState('')

  const params = useMemo(
    () => ({
      category: cat === 'all' ? undefined : cat,
      sort,
      q: search.trim() || undefined,
      limit: 48,
      offset: 0,
    }),
    [cat, sort, search],
  )

  const { data, isLoading } = useTemplates(params)
  const { data: categoriesData } = useTemplateCategories()
  const categories = categoriesData?.categories ?? []
  const items = data?.items ?? []

  const spotlight = items.find((t) => t.featured) ?? items.find((t) => t.is_official) ?? items[0]
  const rest = items.filter((t) => t.id !== spotlight?.id)
  const trending = rest.slice(0, 8)
  const grid = rest.slice(8)

  const open = (t: TemplateListItem) => navigate(APP_ROUTES.TEMPLATE_DETAIL(t.slug))
  const activeCategoryLabel = categories.find((c) => c.id === cat)?.label ?? 'All'

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--bg)]">
      <div className="mx-auto flex max-w-[1180px] flex-col gap-14 px-6 pb-24 pt-10 sm:px-10">
        {/* ── Header ───────────────────────────────────────── */}
        <header className="flex flex-col gap-4">
          <div className="flex items-baseline justify-between gap-6">
            <div>
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--text-faint)]">
                Marketplace
              </div>
              <h1 className="text-[34px] font-semibold leading-[1.1] tracking-tight text-[var(--text)] sm:text-[42px]">
                Templates for every workflow.
              </h1>
              <p className="mt-3 max-w-[560px] text-[14px] leading-relaxed text-[var(--text-mute)]">
                A curated library of ready-made workflows and AI agents.
                Preview, install with one click, or publish your own from
                any workflow you've built.
              </p>
            </div>
            <button
              onClick={() => navigate(APP_ROUTES.MY_TEMPLATES)}
              className="hidden shrink-0 items-center gap-2 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] px-3 py-2 text-[12.5px] font-medium text-[var(--text-mute)] hover:border-[var(--border)] hover:text-[var(--text)] sm:flex"
            >
              <Layers className="h-[13px] w-[13px]" />
              My templates
            </button>
          </div>

          {/* Filter bar */}
          <div className="mt-6 flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <div className="group flex h-[44px] flex-1 items-center gap-2 rounded-[12px] border border-[var(--border-faint)] bg-[var(--surface)] px-4 focus-within:border-[var(--border)]">
                <Search className="h-[15px] w-[15px] shrink-0 text-[var(--text-faint)]" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by tool, use case, or keyword…"
                  className="flex-1 bg-transparent text-[13.5px] text-[var(--text)] outline-none placeholder:text-[var(--text-faint)]"
                />
                {search && (
                  <button onClick={() => setSearch('')} className="text-[var(--text-faint)] hover:text-[var(--text)]">
                    <X size={14} />
                  </button>
                )}
              </div>
              <div className="flex h-[44px] items-center gap-1 rounded-[12px] border border-[var(--border-faint)] bg-[var(--surface)] p-1">
                {SORT_OPTIONS.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setSort(s.id)}
                    className={cn(
                      'flex items-center gap-1.5 rounded-[9px] px-3 py-1.5 text-[12.5px] font-medium transition-colors',
                      sort === s.id
                        ? 'bg-[var(--surface-2)] text-[var(--text)]'
                        : 'text-[var(--text-mute)] hover:text-[var(--text)]',
                    )}
                  >
                    <s.icon className="h-3.5 w-3.5" />
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Category chips */}
            <div className="flex flex-wrap gap-1.5">
              <Chip active={cat === 'all'} onClick={() => setCat('all')}>All</Chip>
              {categories.map((c) => (
                <Chip key={c.id} active={cat === c.id} onClick={() => setCat(c.id)}>
                  {c.label}
                  <span className="ml-1.5 text-[10.5px] text-[var(--text-faint)]">{c.count}</span>
                </Chip>
              ))}
            </div>
          </div>
        </header>

        {isLoading ? (
          <div className="flex items-center justify-center gap-3 py-12 text-[13px] text-[var(--text-faint)]">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading templates…
          </div>
        ) : items.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {/* ── Spotlight ─────────────────────────────── */}
            {spotlight && (
              <section className="flex flex-col gap-3">
                <SectionEyebrow icon={Award} label="Editor's pick" />
                <TemplateCard template={spotlight} variant="spotlight" onClick={() => open(spotlight)} />
              </section>
            )}

            {/* ── Trending scroll row ───────────────────── */}
            {trending.length > 0 && (
              <ScrollRow
                eyebrow={<SectionEyebrow icon={TrendingUp} label="Trending this week" />}
                items={trending}
                onOpen={open}
              />
            )}

            {/* ── Main grid ─────────────────────────────── */}
            {grid.length > 0 && (
              <section className="flex flex-col gap-4">
                <div className="flex items-baseline justify-between">
                  <h2 className="text-[19px] font-semibold tracking-tight text-[var(--text)]">
                    {cat === 'all' ? 'All templates' : `${activeCategoryLabel} templates`}
                  </h2>
                  <span className="text-[12px] text-[var(--text-faint)]">{grid.length} shown</span>
                </div>
                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                  {grid.map((t) => (
                    <TemplateCard key={t.id} template={t} onClick={() => open(t)} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  )
}

// ── Bits ────────────────────────────────────────────────────────

function SectionEyebrow({ icon: Icon, label }: { icon: React.ElementType; label: string }) {
  return (
    <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--text-faint)]">
      <Icon className="h-3.5 w-3.5" />
      {label}
    </div>
  )
}

function Chip({ active, onClick, children }: { active?: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center rounded-full border px-3 py-1 text-[12.5px] font-medium transition-colors',
        active
          ? 'border-[var(--border)] bg-[var(--surface)] text-[var(--text)]'
          : 'border-[var(--border-faint)] text-[var(--text-mute)] hover:border-[var(--border)] hover:text-[var(--text)]',
      )}
    >
      {children}
    </button>
  )
}

function ScrollRow({
  eyebrow,
  items,
  onOpen,
}: {
  eyebrow: React.ReactNode
  items: TemplateListItem[]
  onOpen: (t: TemplateListItem) => void
}) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const nudge = (dx: number) => scrollRef.current?.scrollBy({ left: dx, behavior: 'smooth' })

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        {eyebrow}
        <div className="flex items-center gap-1">
          <button
            onClick={() => nudge(-360)}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--border-faint)] bg-[var(--surface)] text-[var(--text-mute)] hover:border-[var(--border)] hover:text-[var(--text)]"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            onClick={() => nudge(360)}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--border-faint)] bg-[var(--surface)] text-[var(--text-mute)] hover:border-[var(--border)] hover:text-[var(--text)]"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto pb-2 pr-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {items.map((t) => (
          <TemplateCard key={t.id} template={t} variant="list" onClick={() => onOpen(t)} />
        ))}
      </div>
    </section>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-[16px] border border-dashed border-[var(--border-faint)] py-16 text-center">
      <Sparkles className="h-5 w-5 text-[var(--text-faint)]" />
      <div>
        <div className="text-[14.5px] font-semibold text-[var(--text)]">Nothing matches yet</div>
        <div className="mt-1 text-[12.5px] text-[var(--text-mute)]">
          Clear the search or try a different category.
        </div>
      </div>
    </div>
  )
}
