import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Search, Users, X } from 'lucide-react'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useTemplates, useTemplateCategories } from '../hooks/useTemplates'
import { TemplateCard } from '../components/TemplateCard'
import { cn } from '@/lib/cn'
import type { TemplateSort } from '../types/templatesTypes'

/**
 * n8n-style marketplace listing.
 *
 * Left rail: category list + sort. Main area: hero + search + card grid.
 * Cards click through to the detail page.
 */

const SORT_OPTIONS: { id: TemplateSort; label: string }[] = [
  { id: 'newest', label: 'Newest' },
  { id: 'popular', label: 'Most installed' },
  { id: 'price-low', label: 'Price · low → high' },
  { id: 'price-high', label: 'Price · high → low' },
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

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto grid max-w-[1280px] grid-cols-1 gap-8 px-6 pt-10 pb-24 sm:px-10 lg:grid-cols-[220px_1fr]">
        {/* ── Sidebar ─────────────────────────────────────── */}
        <aside className="hidden flex-col gap-6 lg:flex">
          <div>
            <h2 className="mb-2 text-[10.5px] font-semibold uppercase tracking-wider text-text-faint">
              Categories
            </h2>
            <div className="flex flex-col gap-0.5">
              <CategoryLink
                label="All templates"
                count={data?.total ?? 0}
                active={cat === 'all'}
                onClick={() => setCat('all')}
              />
              {categories.map((c) => (
                <CategoryLink
                  key={c.id}
                  label={c.label}
                  count={c.count}
                  active={cat === c.id}
                  onClick={() => setCat(c.id)}
                />
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-2 text-[10.5px] font-semibold uppercase tracking-wider text-text-faint">
              Sort by
            </h2>
            <div className="flex flex-col gap-0.5">
              {SORT_OPTIONS.map((o) => (
                <CategoryLink
                  key={o.id}
                  label={o.label}
                  active={sort === o.id}
                  onClick={() => setSort(o.id)}
                />
              ))}
            </div>
          </div>

          <button
            onClick={() => navigate(APP_ROUTES.MY_TEMPLATES)}
            className="flex items-center gap-2 rounded-[8px] border border-border-faint bg-bg2 px-3 py-2 text-[12.5px] font-medium text-text-mute hover:border-border hover:text-text"
          >
            <Users className="h-[13px] w-[13px]" />
            My templates
          </button>
        </aside>

        {/* ── Main ───────────────────────────────────────── */}
        <main className="flex flex-col gap-6">
          {/* Hero */}
          <header className="flex flex-col gap-3">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-text-faint">
              <span className="inline-flex h-2 w-2 rounded-full bg-accent" />
              Marketplace · {data?.total ?? 0} templates
            </div>
            <h1 className="text-[32px] font-semibold leading-tight tracking-tight text-text sm:text-[38px]">
              Discover ready-made workflows &<br className="hidden sm:block" /> AI agents
            </h1>
            <p className="max-w-[560px] text-[13.5px] leading-relaxed text-text-mute">
              Browse community + official templates. Install one in a click,
              or publish your own to share with the workspace.
            </p>

            {/* Big search bar */}
            <div className="mt-3 flex h-12 items-center gap-2 rounded-[12px] border border-border-faint bg-bg2 px-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)] focus-within:border-border">
              <Search className="h-4 w-4 text-text-faint" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search 4,590+ templates by name, tool, or use case…"
                className="flex-1 bg-transparent text-[14px] text-text outline-none placeholder:text-text-faint"
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="rounded-[6px] p-1 text-text-faint hover:bg-surface hover:text-text"
                >
                  <X size={13} />
                </button>
              )}
            </div>
          </header>

          {/* Mobile category chips */}
          <div className="flex flex-wrap gap-1.5 lg:hidden">
            <ChipButton active={cat === 'all'} onClick={() => setCat('all')}>
              All
            </ChipButton>
            {categories.map((c) => (
              <ChipButton
                key={c.id}
                active={cat === c.id}
                onClick={() => setCat(c.id)}
              >
                {c.label}
              </ChipButton>
            ))}
          </div>

          {/* Grid */}
          {isLoading ? (
            <div className="flex items-center gap-3 py-8 text-[13px] text-text-faint">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading templates…
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 rounded-[14px] border border-dashed border-border-faint py-16 text-center">
              <span className="text-[14px] font-semibold text-text">
                No templates match
              </span>
              <span className="text-[12.5px] text-text-mute">
                Try clearing the search or picking a different category.
              </span>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {items.map((item) => (
                <TemplateCard
                  key={item.id}
                  template={item}
                  onClick={() => navigate(APP_ROUTES.TEMPLATE_DETAIL(item.slug))}
                />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

function CategoryLink({
  label,
  count,
  active,
  onClick,
}: {
  label: string
  count?: number
  active?: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex w-full items-center justify-between rounded-[7px] px-3 py-1.5 text-[13px] transition',
        active
          ? 'bg-surface text-text'
          : 'text-text-mute hover:bg-surface/60 hover:text-text',
      )}
    >
      <span>{label}</span>
      {count !== undefined && (
        <span className="font-mono text-[10.5px] text-text-faint">{count}</span>
      )}
    </button>
  )
}

function ChipButton({
  active,
  onClick,
  children,
}: {
  active?: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'rounded-full border px-3 py-1 text-[11.5px] font-medium transition',
        active
          ? 'border-accent bg-accent/10 text-text'
          : 'border-border-faint text-text-mute hover:border-border hover:text-text',
      )}
    >
      {children}
    </button>
  )
}
