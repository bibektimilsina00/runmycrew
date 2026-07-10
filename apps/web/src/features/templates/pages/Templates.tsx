import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Loader2, Search, Users, Megaphone, HandCoins, Headphones,
  MonitorSmartphone, FolderKanban, MoreHorizontal, Sparkles, LayoutList,
} from 'lucide-react'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useTemplates, useTemplateCategories } from '../hooks/useTemplates'
import { TemplateCard } from '../components/TemplateCard'
import { cn } from '@/lib/cn'
import type { TemplateListItem } from '../types/templatesTypes'

/**
 * n8n workflows-gallery clone. Hero search + category pills, then a
 * curated stack of sections:
 *
 * 1. Newcomer essentials — big featured banner + 2 supporting cards
 * 2. Trending AI templates — 3-col grid
 * 3. Browse by category — big category tiles
 * 4. Featured templates — banner + 3-col grid
 *
 * Everything sourced from the same /templates endpoint; slices happen
 * on the frontend (featured flag + category filter + sort=popular).
 */

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  ai: Sparkles,
  'revenue-ops': HandCoins,
  engineering: MonitorSmartphone,
  inbox: FolderKanban,
  reporting: LayoutList,
  sales: HandCoins,
  loops: Sparkles,
  marketing: Megaphone,
  support: Headphones,
  'it-ops': MonitorSmartphone,
  'document-ops': FolderKanban,
  other: MoreHorizontal,
}

export function Templates() {
  const navigate = useNavigate()
  const [cat, setCat] = useState<string>('all')
  const [search, setSearch] = useState('')

  const params = useMemo(
    () => ({
      category: cat === 'all' ? undefined : cat,
      sort: 'popular' as const,
      q: search.trim() || undefined,
      limit: 60,
      offset: 0,
    }),
    [cat, search],
  )

  const { data, isLoading } = useTemplates(params)
  const { data: categoriesData } = useTemplateCategories()
  const categories = categoriesData?.categories ?? []
  const items = data?.items ?? []

  const featured = items.find((t) => t.featured || t.is_official) ?? items[0]
  const newcomerRest = items.filter((t) => t.id !== featured?.id).slice(0, 3)
  const trending = items.slice(3, 9)
  const featuredBanner = items[Math.min(9, items.length - 1)]
  const featuredGrid = items.slice(10, 16)

  const open = (t: TemplateListItem) => navigate(APP_ROUTES.TEMPLATE_DETAIL(t.slug))

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-14 px-6 pt-16 pb-24 sm:px-10">
        {/* ── Hero: search + category pills ─────────────── */}
        <header className="flex flex-col items-center gap-6">
          <div className="flex h-14 w-full max-w-[720px] items-center gap-3 rounded-full border border-border-faint bg-bg2 px-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] focus-within:border-border">
            <Search className="h-4 w-4 text-text-faint" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search apps, roles, usecases…"
              className="flex-1 bg-transparent text-[15px] text-text outline-none placeholder:text-text-faint"
            />
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            <CategoryPill active={cat === 'all'} onClick={() => setCat('all')}>All</CategoryPill>
            {categories.map((c) => (
              <CategoryPill
                key={c.id}
                active={cat === c.id}
                onClick={() => setCat(c.id)}
              >
                {c.label}
              </CategoryPill>
            ))}
          </div>
          <button
            onClick={() => navigate(APP_ROUTES.MY_TEMPLATES)}
            className="flex items-center gap-2 rounded-[8px] border border-border-faint bg-bg2 px-3 py-2 text-[12.5px] font-medium text-text-mute hover:border-border hover:text-text"
          >
            <Users className="h-[13px] w-[13px]" />
            My templates
          </button>
        </header>

        {isLoading ? (
          <div className="flex items-center justify-center gap-3 py-12 text-[13px] text-text-faint">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading templates…
          </div>
        ) : items.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {/* ── Newcomer essentials ─────────────────── */}
            {featured && (
              <Section title="Newcomer essentials: learn by doing">
                <TemplateCard template={featured} variant="featured" onClick={() => open(featured)} />
                {newcomerRest.length > 0 && (
                  <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {newcomerRest.map((t) => (
                      <TemplateCard key={t.id} template={t} onClick={() => open(t)} />
                    ))}
                  </div>
                )}
              </Section>
            )}

            {/* ── Trending AI templates ───────────────── */}
            {trending.length > 0 && (
              <Section
                title={
                  <span className="flex items-center gap-2">
                    Trending{' '}
                    <span className="rounded-[7px] border border-border-faint bg-bg2 px-2 py-0.5 text-[16px] font-medium text-text">
                      AI
                    </span>{' '}
                    templates
                  </span>
                }
              >
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {trending.map((t) => (
                    <TemplateCard key={t.id} template={t} onClick={() => open(t)} />
                  ))}
                </div>
                <button
                  onClick={() => setCat('ai')}
                  className="mt-4 text-[13px] font-medium text-text-mute hover:text-text"
                >
                  Explore more <span className="rounded-[6px] border border-border-faint bg-bg2 px-1.5 py-0.5 text-[12px] text-text">AI</span> templates →
                </button>
              </Section>
            )}

            {/* ── Browse by category ──────────────────── */}
            {categories.length > 0 && (
              <Section title="Browse by category">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {categories.map((c) => {
                    const Icon = CATEGORY_ICONS[c.id] ?? MoreHorizontal
                    return (
                      <button
                        key={c.id}
                        onClick={() => setCat(c.id)}
                        className="group flex items-center gap-5 rounded-[16px] border border-border-faint bg-bg2 px-6 py-5 text-left transition-colors hover:border-border hover:bg-bg2/70"
                      >
                        <span className="flex h-14 w-14 items-center justify-center rounded-[12px] bg-surface text-text-mute group-hover:text-text">
                          <Icon className="h-6 w-6" strokeWidth={1.5} />
                        </span>
                        <div>
                          <div className="text-[17px] font-semibold text-text">{c.label}</div>
                          <div className="mt-0.5 text-[12px] text-text-faint">{c.count} templates</div>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </Section>
            )}

            {/* ── Featured templates ──────────────────── */}
            {featuredBanner && featuredGrid.length > 0 && (
              <Section title="Featured templates">
                <TemplateCard template={featuredBanner} variant="featured" onClick={() => open(featuredBanner)} />
                <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {featuredGrid.map((t) => (
                    <TemplateCard key={t.id} template={t} onClick={() => open(t)} />
                  ))}
                </div>
              </Section>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function Section({ title, children }: { title: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-[26px] font-semibold tracking-tight text-text">{title}</h2>
      <div>{children}</div>
    </section>
  )
}

function CategoryPill({
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
        'rounded-full border px-4 py-1.5 text-[13px] font-medium transition',
        active
          ? 'border-text bg-text/[0.08] text-text'
          : 'border-border-faint text-text-mute hover:border-border hover:text-text',
      )}
    >
      {children}
    </button>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-[16px] border border-dashed border-border-faint py-16 text-center">
      <span className="text-[14px] font-semibold text-text">No templates match</span>
      <span className="text-[12.5px] text-text-mute">
        Try clearing the search or picking a different category.
      </span>
    </div>
  )
}
