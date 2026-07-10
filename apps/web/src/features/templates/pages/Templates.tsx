import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Loader2, Search, Users, Megaphone, HandCoins, Headphones,
  MonitorSmartphone, FolderKanban, MoreHorizontal, Sparkles, LayoutList,
  BarChart3, Layers,
} from 'lucide-react'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useTemplates, useTemplateCategories } from '../hooks/useTemplates'
import { TemplateCard } from '../components/TemplateCard'
import { cn } from '@/lib/cn'
import type { TemplateListItem } from '../types/templatesTypes'

/**
 * n8n workflows-gallery, adapted to our theme.
 *
 * Layout is a vertical stack of sections separated by generous
 * whitespace. Cards are dark tiles matching the app's surface tokens —
 * no washed-out pastels. Everything sits inside a single 1200px
 * container so line lengths stay comfortable.
 */

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  ai: Sparkles,
  'revenue-ops': BarChart3,
  engineering: MonitorSmartphone,
  inbox: FolderKanban,
  reporting: LayoutList,
  sales: HandCoins,
  loops: Layers,
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

  const featured = items.find((t) => t.featured) ?? items.find((t) => t.is_official) ?? items[0]
  const newcomerRest = items.filter((t) => t.id !== featured?.id).slice(0, 3)
  const trending = items.slice(3, 9)
  const featuredBanner = items[Math.min(9, items.length - 1)]
  const featuredGrid = items.slice(10, 16)

  const open = (t: TemplateListItem) => navigate(APP_ROUTES.TEMPLATE_DETAIL(t.slug))

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--bg)]">
      <div className="mx-auto flex max-w-[1240px] flex-col gap-20 px-6 pt-20 pb-32 sm:px-10">
        {/* ── Hero ────────────────────────────────────────── */}
        <header className="flex flex-col items-center gap-6">
          <div className="w-full max-w-[720px]">
            <div className="group flex h-[60px] items-center gap-3 rounded-[16px] border border-[var(--border-faint)] bg-[var(--surface)] px-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.03),0_18px_50px_-24px_rgba(0,0,0,0.55)] focus-within:border-[var(--border)]">
              <Search className="h-[18px] w-[18px] shrink-0 text-[var(--text-faint)]" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search apps, roles, use cases…"
                className="flex-1 bg-transparent text-[15px] text-[var(--text)] outline-none placeholder:text-[var(--text-faint)]"
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="text-[12px] text-[var(--text-faint)] hover:text-[var(--text)]"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-2">
            <CategoryPill active={cat === 'all'} onClick={() => setCat('all')}>All</CategoryPill>
            {categories.map((c) => (
              <CategoryPill key={c.id} active={cat === c.id} onClick={() => setCat(c.id)}>
                {c.label}
              </CategoryPill>
            ))}
          </div>

          <button
            onClick={() => navigate(APP_ROUTES.MY_TEMPLATES)}
            className="mt-2 flex items-center gap-1.5 text-[12.5px] font-medium text-[var(--text-faint)] hover:text-[var(--text)]"
          >
            <Users className="h-[13px] w-[13px]" />
            My templates
          </button>
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
            {/* ── Newcomer essentials ─────────────────── */}
            {featured && (
              <Section title="Newcomer essentials: learn by doing">
                <TemplateCard template={featured} variant="featured" onClick={() => open(featured)} />
                {newcomerRest.length > 0 && (
                  <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {newcomerRest.map((t) => (
                      <TemplateCard key={t.id} template={t} onClick={() => open(t)} />
                    ))}
                  </div>
                )}
              </Section>
            )}

            {/* ── Trending ────────────────────────────── */}
            {trending.length > 0 && (
              <Section
                title={
                  <span className="flex items-center gap-3">
                    Trending
                    <span className="rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] px-2.5 py-0.5 text-[20px] font-semibold leading-none text-[var(--text)]">
                      AI
                    </span>
                    templates
                  </span>
                }
              >
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                  {trending.map((t) => (
                    <TemplateCard key={t.id} template={t} onClick={() => open(t)} />
                  ))}
                </div>
                <button
                  onClick={() => setCat('ai')}
                  className="mt-6 flex items-center gap-2 text-[13.5px] font-medium text-[var(--text-mute)] hover:text-[var(--text)]"
                >
                  Explore more
                  <span className="rounded-[6px] border border-[var(--border-faint)] bg-[var(--surface)] px-2 py-0.5 text-[13px] text-[var(--text)]">AI</span>
                  templates →
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
                        className="group flex h-[112px] items-center gap-5 overflow-hidden rounded-[18px] border border-[var(--border-faint)] bg-[var(--surface)] px-6 text-left transition-all hover:-translate-y-0.5 hover:border-[var(--border)] hover:bg-[var(--surface-2)]"
                      >
                        <span className="flex h-[62px] w-[62px] shrink-0 items-center justify-center rounded-[14px] bg-[var(--surface-2)] text-[var(--text-mute)] transition-colors group-hover:bg-[var(--surface-3)] group-hover:text-[var(--text)]">
                          <Icon className="h-7 w-7" strokeWidth={1.4} />
                        </span>
                        <div className="min-w-0">
                          <div className="text-[19px] font-semibold tracking-tight text-[var(--text)]">
                            {c.label}
                          </div>
                          <div className="mt-1 text-[12px] text-[var(--text-faint)]">
                            {c.count} template{c.count === 1 ? '' : 's'}
                          </div>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </Section>
            )}

            {/* ── Featured templates ──────────────────── */}
            {featuredBanner && (
              <Section title="Featured templates">
                <TemplateCard template={featuredBanner} variant="featured" onClick={() => open(featuredBanner)} />
                {featuredGrid.length > 0 && (
                  <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {featuredGrid.map((t) => (
                      <TemplateCard key={t.id} template={t} onClick={() => open(t)} />
                    ))}
                  </div>
                )}
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
    <section>
      <h2 className="mb-6 text-[28px] font-semibold leading-tight tracking-tight text-[var(--text)] sm:text-[30px]">
        {title}
      </h2>
      {children}
    </section>
  )
}

function CategoryPill({ active, onClick, children }: { active?: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'rounded-full border px-4 py-1.5 text-[13px] font-medium transition-colors',
        active
          ? 'border-[var(--border)] bg-[var(--surface)] text-[var(--text)]'
          : 'border-[var(--border-faint)] text-[var(--text-mute)] hover:border-[var(--border)] hover:text-[var(--text)]',
      )}
    >
      {children}
    </button>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-[18px] border border-dashed border-[var(--border-faint)] py-16 text-center">
      <span className="text-[15px] font-semibold text-[var(--text)]">No templates match</span>
      <span className="text-[13px] text-[var(--text-mute)]">
        Try clearing the search or picking a different category.
      </span>
    </div>
  )
}
