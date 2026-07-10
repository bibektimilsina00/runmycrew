import { ArrowUpRight, BadgeCheck, Download, Clock } from 'lucide-react'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'
import { TemplateGraphPreview } from './TemplateGraphPreview'
import type { TemplateListItem } from '../types/templatesTypes'

interface Props {
  template: TemplateListItem
  onClick?: () => void
  /**
   * ``spotlight`` — 2:1 horizontal card used at the top of the page.
   * ``grid`` — 1:1-ish tile used in the main grid.
   * ``list`` — dense horizontal row used in scrollable rows.
   */
  variant?: 'spotlight' | 'grid' | 'list'
}

/**
 * Fresh direction — a "workflow card as a product tile":
 *
 * - Every card has a real preview (graph render) at the top or the side.
 * - Below the preview: category chip + title + creator + metric row
 *   (installs, updated).
 * - Integration icons live in a compact strip pinned to the bottom
 *   of the card so titles + previews never fight for the same space.
 * - Hover lifts the whole card + reveals an "open" arrow.
 *
 * Nothing about the visual language borrows from n8n — this is closer
 * to Vercel's deploy-template grid or Framer's marketplace tiles.
 */
export function TemplateCard({ template, onClick, variant = 'grid' }: Props) {
  if (variant === 'spotlight') return <SpotlightCard t={template} onClick={onClick} />
  if (variant === 'list') return <ListCard t={template} onClick={onClick} />
  return <GridCard t={template} onClick={onClick} />
}

// ── Spotlight ────────────────────────────────────────────────────

function SpotlightCard({ t, onClick }: { t: TemplateListItem; onClick?: () => void }) {
  const integrations = deriveIntegrations(t)
  return (
    <button
      type="button"
      onClick={onClick}
      className="group relative flex w-full flex-col gap-6 overflow-hidden rounded-[20px] border border-[var(--border-faint)] bg-[var(--surface)] p-6 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--border)] hover:shadow-[0_28px_60px_-24px_rgba(0,0,0,0.6)] sm:flex-row sm:p-8"
    >
      {/* Preview column */}
      <div className={`relative flex aspect-video w-full shrink-0 items-center justify-center overflow-hidden rounded-[14px] ${t.bg_variant || 'inspo-bg-1'} sm:h-[240px] sm:w-[420px]`}>
        <span className="pointer-events-none absolute inset-0 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]" />
        {t.graph?.nodes?.length ? (
          <div className="absolute inset-0 p-4">
            <div className="h-full w-full overflow-hidden rounded-[10px] border border-white/12 bg-black/35 backdrop-blur">
              <TemplateGraphPreview graph={t.graph} static />
            </div>
          </div>
        ) : (
          <span className="text-[13px] text-white/50">no preview</span>
        )}
      </div>

      {/* Copy column */}
      <div className="flex min-w-0 flex-1 flex-col gap-5">
        <div className="flex items-center gap-2">
          <CategoryChip category={t.category} />
          {t.is_official && <span className="rounded-full border border-[var(--accent)]/40 bg-[var(--accent)]/10 px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wider text-[var(--accent)]">Official</span>}
          {t.featured && !t.is_official && <span className="rounded-full border border-[var(--border-soft)] bg-[var(--surface-2)] px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wider text-[var(--text-mute)]">Featured</span>}
        </div>
        <h3 className="line-clamp-3 text-[24px] font-semibold leading-[1.2] tracking-tight text-[var(--text)] sm:text-[28px]">
          {t.title}
        </h3>
        {t.summary && (
          <p className="line-clamp-2 max-w-[560px] text-[13.5px] leading-relaxed text-[var(--text-mute)]">
            {t.summary}
          </p>
        )}

        <div className="mt-auto flex flex-wrap items-center gap-4 border-t border-[var(--border-faint)] pt-4">
          {integrations.length > 0 && (
            <div className="flex items-center gap-1.5">
              {integrations.slice(0, 5).map((slug) => (
                <IntegrationTile key={slug} slug={slug} size="md" />
              ))}
              {integrations.length > 5 && (
                <span className="rounded-[7px] border border-[var(--border-faint)] bg-[var(--bg)] px-2 py-1 text-[11.5px] font-semibold text-[var(--text-mute)]">
                  +{integrations.length - 5}
                </span>
              )}
            </div>
          )}
          <div className="ml-auto flex items-center gap-4 text-[11.5px] text-[var(--text-faint)]">
            <span className="flex items-center gap-1"><Download className="h-3 w-3" /> {t.download_count.toLocaleString()}</span>
            <CreatorRow t={t} />
          </div>
        </div>
      </div>

      <ArrowUpRight className="pointer-events-none absolute right-6 top-6 h-4 w-4 text-[var(--text-faint)] transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-[var(--text)] sm:right-8 sm:top-8" />
    </button>
  )
}

// ── Grid tile ────────────────────────────────────────────────────

function GridCard({ t, onClick }: { t: TemplateListItem; onClick?: () => void }) {
  const integrations = deriveIntegrations(t)
  return (
    <button
      type="button"
      onClick={onClick}
      className="group relative flex h-full flex-col overflow-hidden rounded-[16px] border border-[var(--border-faint)] bg-[var(--surface)] text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--border)] hover:shadow-[0_20px_44px_-20px_rgba(0,0,0,0.55)]"
    >
      {/* Preview slab */}
      <div className={`relative flex h-[152px] w-full items-center justify-center overflow-hidden ${t.bg_variant || 'inspo-bg-1'}`}>
        <span className="pointer-events-none absolute inset-0 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]" />
        {t.graph?.nodes?.length ? (
          <div className="absolute inset-3">
            <div className="h-full w-full overflow-hidden rounded-[8px] border border-white/12 bg-black/35 backdrop-blur">
              <TemplateGraphPreview graph={t.graph} static />
            </div>
          </div>
        ) : null}
        <div className="absolute left-3 top-3 flex items-center gap-1.5">
          <CategoryChip category={t.category} onDark />
        </div>
        {(t.is_premium && t.price_cents > 0) ? (
          <span className="absolute right-3 top-3 rounded-full bg-black/40 px-2.5 py-0.5 text-[10.5px] font-semibold text-white/85 backdrop-blur">
            {formatPrice(t.price_cents)}
          </span>
        ) : (
          <span className="absolute right-3 top-3 rounded-full bg-black/40 px-2.5 py-0.5 text-[10.5px] font-semibold text-white/85 backdrop-blur">
            Free
          </span>
        )}
      </div>

      {/* Body */}
      <div className="flex flex-1 flex-col gap-3 p-5">
        <h3 className="line-clamp-2 text-[15.5px] font-semibold leading-[1.35] tracking-tight text-[var(--text)]">
          {t.title}
        </h3>
        {t.summary && (
          <p className="line-clamp-2 text-[12px] leading-snug text-[var(--text-mute)]">
            {t.summary}
          </p>
        )}

        <div className="mt-auto flex items-center justify-between gap-3 border-t border-[var(--border-faint)] pt-3">
          {integrations.length > 0 ? (
            <div className="flex items-center gap-1">
              {integrations.slice(0, 4).map((slug) => (
                <IntegrationTile key={slug} slug={slug} size="sm" />
              ))}
              {integrations.length > 4 && (
                <span className="ml-0.5 text-[10.5px] font-semibold text-[var(--text-faint)]">
                  +{integrations.length - 4}
                </span>
              )}
            </div>
          ) : <span />}
          <CreatorRow t={t} compact />
        </div>
      </div>
    </button>
  )
}

// ── List row ─────────────────────────────────────────────────────

function ListCard({ t, onClick }: { t: TemplateListItem; onClick?: () => void }) {
  const integrations = deriveIntegrations(t)
  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex w-full min-w-[320px] max-w-[360px] shrink-0 flex-col gap-4 rounded-[14px] border border-[var(--border-faint)] bg-[var(--surface)] p-5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--border)]"
    >
      <div className={`relative flex h-[108px] w-full items-center justify-center overflow-hidden rounded-[10px] ${t.bg_variant || 'inspo-bg-1'}`}>
        {t.graph?.nodes?.length ? (
          <div className="absolute inset-2 overflow-hidden rounded-[6px] border border-white/10 bg-black/30 backdrop-blur">
            <TemplateGraphPreview graph={t.graph} static />
          </div>
        ) : null}
      </div>
      <div className="flex flex-1 flex-col gap-2">
        <div className="flex items-center gap-2">
          <CategoryChip category={t.category} />
        </div>
        <h3 className="line-clamp-2 text-[14px] font-semibold leading-snug text-[var(--text)]">{t.title}</h3>
        <div className="mt-auto flex items-center justify-between gap-3">
          <div className="flex items-center gap-1">
            {integrations.slice(0, 3).map((slug) => (
              <IntegrationTile key={slug} slug={slug} size="sm" />
            ))}
          </div>
          <span className="text-[10.5px] text-[var(--text-faint)]">{t.download_count.toLocaleString()} installs</span>
        </div>
      </div>
    </button>
  )
}

// ── Building blocks ──────────────────────────────────────────────

function IntegrationTile({ slug, size }: { slug: string; size: 'sm' | 'md' }) {
  const cls =
    size === 'md'
      ? 'flex h-8 w-8 items-center justify-center overflow-hidden rounded-[7px] bg-[var(--bg)] shadow-[inset_0_0_0_1px_var(--border-faint)] [&_img]:h-5 [&_img]:w-5 [&_img]:object-contain'
      : 'flex h-6 w-6 items-center justify-center overflow-hidden rounded-[6px] bg-[var(--bg)] shadow-[inset_0_0_0_1px_var(--border-faint)] [&_img]:h-4 [&_img]:w-4 [&_img]:object-contain'
  return (
    <span className={cls} title={slug}>
      <BrandIcon slug={slug} />
    </span>
  )
}

function CategoryChip({ category, onDark }: { category: string; onDark?: boolean }) {
  const cls = onDark
    ? 'rounded-full border border-white/12 bg-black/40 px-2.5 py-0.5 text-[10.5px] font-semibold uppercase tracking-wider text-white/85 backdrop-blur'
    : 'rounded-full border border-[var(--border-faint)] bg-[var(--bg)] px-2.5 py-0.5 text-[10.5px] font-semibold uppercase tracking-wider text-[var(--text-mute)]'
  return <span className={cls}>{humanCategory(category)}</span>
}

function CreatorRow({ t, compact }: { t: TemplateListItem; compact?: boolean }) {
  const label = t.creator?.full_name || t.creator?.email?.split('@')[0] || (t.is_official ? 'Official' : 'Community')
  const initial = (label ?? '?').trim().charAt(0).toUpperCase()
  return (
    <div className="flex items-center gap-2 text-[11.5px] text-[var(--text-mute)]">
      <span className="flex h-6 w-6 shrink-0 items-center justify-center overflow-hidden rounded-full border border-[var(--border-faint)] bg-[var(--bg)] text-[10.5px] font-semibold text-[var(--text-mute)]">
        {t.creator?.avatar_url ? (
          <img src={t.creator.avatar_url} alt={label ?? ''} className="h-full w-full object-cover" />
        ) : (
          initial
        )}
      </span>
      {!compact && <span className="truncate">{label}</span>}
      {t.is_official && <BadgeCheck className="h-3.5 w-3.5 shrink-0 text-[var(--accent)]" />}
      {!compact && (
        <>
          <span className="text-[var(--text-faint)]">·</span>
          <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {timeAgo(t.updated_at)}</span>
        </>
      )}
    </div>
  )
}

// ── Helpers ─────────────────────────────────────────────────────

const CONTROL_TYPES = new Set([
  'chat_app', 'manual', 'cron', 'webhook', 'trigger',
  'set_variable', 'merge', 'switch', 'condition', 'delay', 'wait',
  'json_transform', 'code', 'sub_workflow', 'sub_crew', 'route_to',
])

function deriveIntegrations(t: TemplateListItem): string[] {
  const s = new Set<string>()
  for (const id of t.tools_required ?? []) s.add(id.toLowerCase())
  for (const node of t.graph?.nodes ?? []) {
    const type = node.type ?? ''
    const brand = type.split('.').pop()
    if (brand && !CONTROL_TYPES.has(brand)) s.add(brand.toLowerCase())
  }
  return Array.from(s)
}

function humanCategory(c: string): string {
  return c.split('-').map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')
}

function formatPrice(cents: number): string {
  if (!cents) return 'Free'
  const dollars = cents / 100
  return Number.isInteger(dollars) ? `$${dollars}` : `$${dollars.toFixed(2)}`
}

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime()
  if (!then) return '—'
  const diff = Date.now() - then
  const day = 86400_000
  if (diff < day) return 'today'
  if (diff < 7 * day) return `${Math.floor(diff / day)}d ago`
  if (diff < 30 * day) return `${Math.floor(diff / (7 * day))}w ago`
  if (diff < 365 * day) return `${Math.floor(diff / (30 * day))}mo ago`
  return `${Math.floor(diff / (365 * day))}y ago`
}
