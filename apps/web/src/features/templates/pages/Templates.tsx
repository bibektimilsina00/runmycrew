import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, X, Sparkles, TrendingUp, Clock, Layers } from 'lucide-react'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useTemplates, useTemplateCategories } from '../hooks/useTemplates'
import { TemplateCard } from '../components/TemplateCard'
import { cn } from '@/lib/cn'
import type { TemplateListItem, TemplateSort } from '../types/templatesTypes'

/**
 * Templates gallery. One surface: a uniform grid where every card
 * leads with a live render of its own workflow graph (MiniGraph).
 * The preview IS the design — the page chrome around it stays quiet:
 * header, search + sort, category chips, grid. No spotlight banner,
 * no scroll rows, no section switching.
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

  const open = (t: TemplateListItem) => navigate(APP_ROUTES.TEMPLATE_DETAIL(t.slug))
  const activeCategoryLabel = categories.find((c) => c.id === cat)?.label ?? 'All'

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--bg)]">
      <div className="mx-auto flex max-w-[1180px] flex-col gap-8 px-6 pb-24 pt-10 sm:px-10">
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
              className="hidden shrink-0 cursor-pointer items-center gap-2 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] px-3 py-2 text-[12.5px] font-medium text-[var(--text-mute)] transition-colors hover:border-[var(--border)] hover:text-[var(--text)] sm:flex"
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
                  <button
                    onClick={() => setSearch('')}
                    aria-label="Clear search"
                    className="cursor-pointer text-[var(--text-faint)] hover:text-[var(--text)]"
                  >
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
                      'flex cursor-pointer items-center gap-1.5 rounded-[9px] px-3 py-1.5 text-[12.5px] font-medium transition-colors',
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

        {/* ── Grid ─────────────────────────────────────────── */}
        {isLoading ? (
          <SkeletonGrid />
        ) : items.length === 0 ? (
          <EmptyState />
        ) : (
          <section className="flex flex-col gap-4">
            <div className="flex items-baseline justify-between">
              <h2 className="text-[19px] font-semibold tracking-tight text-[var(--text)]">
                {cat === 'all' ? 'All templates' : `${activeCategoryLabel} templates`}
              </h2>
              <span className="text-[12px] text-[var(--text-faint)]">
                {items.length} {items.length === 1 ? 'template' : 'templates'}
              </span>
            </div>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((t) => (
                <TemplateCard key={t.id} template={t} onClick={() => open(t)} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

// ── Bits ────────────────────────────────────────────────────────

function Chip({ active, onClick, children }: { active?: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex cursor-pointer items-center rounded-full border px-3 py-1 text-[12.5px] font-medium transition-colors',
        active
          ? 'border-[var(--border)] bg-[var(--surface)] text-[var(--text)]'
          : 'border-[var(--border-faint)] text-[var(--text-mute)] hover:border-[var(--border)] hover:text-[var(--text)]',
      )}
    >
      {children}
    </button>
  )
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 9 }, (_, i) => (
        <div
          key={i}
          className="animate-pulse overflow-hidden rounded-[14px] border border-[var(--border-faint)] bg-[var(--surface)]"
        >
          <div className="aspect-[16/10] w-full border-b border-[var(--border-faint)] bg-[var(--surface-2)]/50" />
          <div className="flex flex-col gap-2.5 p-4">
            <div className="h-4 w-3/4 rounded bg-[var(--surface-2)]" />
            <div className="h-3.5 w-1/2 rounded bg-[var(--surface-2)]/70" />
          </div>
        </div>
      ))}
    </div>
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
