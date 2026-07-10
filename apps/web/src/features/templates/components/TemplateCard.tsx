import { ArrowUpRight, BadgeCheck, Clock, Download } from 'lucide-react'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'
import type { TemplateListItem } from '../types/templatesTypes'

interface Props {
  template: TemplateListItem
  onClick?: () => void
  variant?: 'spotlight' | 'grid' | 'list'
}

/**
 * Flat dark-tile template card. No gradient/preview backgrounds —
 * they always looked muddy behind small type. Node icons are shown
 * as a stacked strip at the bottom (avatar-pile style: each tile
 * sits partway over the previous one), with a "+N" chip when more
 * than a handful of integrations are used.
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
      className="group relative flex w-full flex-col gap-4 overflow-hidden rounded-[16px] border border-[var(--border-faint)] bg-[var(--surface)] p-7 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--border)] hover:shadow-[0_24px_50px_-24px_rgba(0,0,0,0.55)] sm:p-9"
    >
      <div className="flex items-center gap-2">
        <CategoryChip category={t.category} />
        {t.is_official && (
          <span className="rounded-full border border-[var(--accent)]/40 bg-[var(--accent)]/10 px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wider text-[var(--accent)]">
            Official
          </span>
        )}
        {t.featured && !t.is_official && (
          <span className="rounded-full border border-[var(--border-soft)] bg-[var(--surface-2)] px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wider text-[var(--text-mute)]">
            Featured
          </span>
        )}
      </div>

      <h3 className="line-clamp-2 max-w-[720px] text-[26px] font-semibold leading-[1.15] tracking-tight text-[var(--text)] sm:text-[32px]">
        {t.title}
      </h3>

      {t.summary && (
        <p className="line-clamp-2 max-w-[640px] text-[14px] leading-relaxed text-[var(--text-mute)]">
          {t.summary}
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-6 border-t border-[var(--border-faint)] pt-4">
        <IconStack integrations={integrations} max={6} />
        <div className="ml-auto flex items-center gap-4 text-[12px] text-[var(--text-mute)]">
          <span className="flex items-center gap-1.5">
            <Download className="h-3.5 w-3.5" />
            {t.download_count.toLocaleString()}
          </span>
          <span className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            {timeAgo(t.updated_at)}
          </span>
          <CreatorRow t={t} compact />
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
      className="group relative flex h-[196px] w-full flex-col justify-between overflow-hidden rounded-[14px] border border-[var(--border-faint)] bg-[var(--surface)] p-5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--border)] hover:bg-[var(--surface-2)] hover:shadow-[0_20px_40px_-24px_rgba(0,0,0,0.55)]"
    >
      <div className="flex items-start justify-between gap-2">
        <CategoryChip category={t.category} />
        <ArrowUpRight className="h-4 w-4 shrink-0 text-[var(--text-faint)] opacity-0 transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-[var(--text)] group-hover:opacity-100" />
      </div>

      <h3 className="my-3 line-clamp-3 text-[15.5px] font-semibold leading-[1.35] tracking-tight text-[var(--text)]">
        {t.title}
      </h3>

      <div className="flex items-end justify-between gap-3">
        <IconStack integrations={integrations} max={4} />
        <CreatorRow t={t} compact />
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
      className="group flex h-[168px] w-[300px] shrink-0 flex-col justify-between rounded-[13px] border border-[var(--border-faint)] bg-[var(--surface)] p-4 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--border)] hover:bg-[var(--surface-2)]"
    >
      <div className="flex items-start justify-between">
        <CategoryChip category={t.category} />
        <ArrowUpRight className="h-3.5 w-3.5 shrink-0 text-[var(--text-faint)] opacity-0 transition-all group-hover:opacity-100" />
      </div>
      <h3 className="my-2 line-clamp-3 text-[13.5px] font-semibold leading-snug text-[var(--text)]">
        {t.title}
      </h3>
      <div className="flex items-end justify-between gap-2">
        <IconStack integrations={integrations} max={3} tight />
        <span className="text-[10.5px] text-[var(--text-faint)]">
          {t.download_count.toLocaleString()}
        </span>
      </div>
    </button>
  )
}

// ── Icon stack (avatar-pile) ────────────────────────────────────

function IconStack({
  integrations,
  max,
  tight,
}: {
  integrations: string[]
  max: number
  tight?: boolean
}) {
  const shown = integrations.slice(0, max)
  const overflow = Math.max(0, integrations.length - max)
  const tileSize = tight ? 26 : 32
  const overlap = tight ? 8 : 10 // negative margin
  return (
    <div className="flex items-center">
      <div className="flex items-center">
        {shown.map((slug, i) => (
          <span
            key={slug}
            style={{ marginLeft: i === 0 ? 0 : -overlap, zIndex: shown.length - i }}
            className="relative flex items-center justify-center overflow-hidden rounded-[7px] border border-[var(--border-faint)] bg-[var(--surface-2)] shadow-[0_2px_6px_-2px_rgba(0,0,0,0.5)] [&_img]:object-contain"
            title={slug}
          >
            <span
              style={{
                width: tileSize,
                height: tileSize,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <BrandIcon
                slug={slug}
                style={{ width: tileSize - 12, height: tileSize - 12 }}
              />
            </span>
          </span>
        ))}
      </div>
      {overflow > 0 && (
        <span
          style={{ marginLeft: -overlap, zIndex: 0 }}
          className={`relative flex items-center justify-center rounded-[7px] border border-[var(--border-faint)] bg-[var(--surface-2)] font-semibold text-[var(--text-mute)] ${
            tight ? 'h-[26px] min-w-[30px] px-1.5 text-[10.5px]' : 'h-[32px] min-w-[36px] px-2 text-[11.5px]'
          }`}
        >
          +{overflow}
        </span>
      )}
    </div>
  )
}

// ── Building blocks ──────────────────────────────────────────────

function CategoryChip({ category }: { category: string }) {
  return (
    <span className="rounded-full border border-[var(--border-faint)] bg-[var(--bg)] px-2.5 py-0.5 text-[10.5px] font-semibold uppercase tracking-wider text-[var(--text-mute)]">
      {humanCategory(category)}
    </span>
  )
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
