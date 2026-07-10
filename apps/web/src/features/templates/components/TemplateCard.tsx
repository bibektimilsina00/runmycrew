import { BadgeCheck } from 'lucide-react'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'
import { TemplateGraphPreview } from './TemplateGraphPreview'
import type { TemplateListItem } from '../types/templatesTypes'

interface Props {
  template: TemplateListItem
  onClick?: () => void
  variant?: 'grid' | 'featured'
}

/**
 * Template card — n8n workflows-page style.
 *
 * Two variants:
 *
 * - **grid** — flat dark tile with title dominant, integration icons
 *   at the bottom-left, creator pip at the bottom-right. No summary
 *   text (matches n8n; title carries the meaning).
 *
 * - **featured** — banner-height card with the theme gradient behind,
 *   headline + integrations on the left, a mini schematic on the
 *   right. The pip floats over the right pane.
 */
export function TemplateCard({ template, onClick, variant = 'grid' }: Props) {
  if (variant === 'featured') return <FeaturedCard template={template} onClick={onClick} />
  return <GridCard template={template} onClick={onClick} />
}

// ── Grid variant ─────────────────────────────────────────────────

function GridCard({ template, onClick }: { template: TemplateListItem; onClick?: () => void }) {
  const integrations = deriveIntegrations(template)
  const shown = integrations.slice(0, 3)
  const overflow = Math.max(0, integrations.length - 3)

  return (
    <button
      type="button"
      onClick={onClick}
      className="group relative flex h-[196px] w-full flex-col overflow-hidden rounded-[16px] border border-[var(--border-faint)] bg-[var(--surface)] p-6 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--border)] hover:bg-[var(--surface-2)]"
    >
      <div className="flex-1">
        <h3 className="line-clamp-3 pr-8 text-[16.5px] font-semibold leading-[1.4] tracking-tight text-[var(--text)]">
          {template.title}
        </h3>
      </div>

      <div className="flex items-end justify-between gap-3">
        <IntegrationStrip integrations={shown} overflow={overflow} />
        <CreatorPip creator={template.creator} isOfficial={template.is_official} />
      </div>
    </button>
  )
}

// ── Featured variant ─────────────────────────────────────────────

function FeaturedCard({ template, onClick }: { template: TemplateListItem; onClick?: () => void }) {
  const integrations = deriveIntegrations(template)
  const shown = integrations.slice(0, 3)
  const overflow = Math.max(0, integrations.length - 3)
  const bg = template.bg_variant || 'inspo-bg-1'

  return (
    <button
      type="button"
      onClick={onClick}
      className={`group relative flex w-full overflow-hidden rounded-[18px] border border-white/10 text-left transition-transform duration-200 hover:-translate-y-0.5 ${bg}`}
    >
      {/* Inner glow */}
      <span className="pointer-events-none absolute inset-0 rounded-[18px] shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]" />

      <div className="relative z-10 flex flex-1 flex-col justify-between px-8 py-8 sm:px-10 sm:py-10">
        <div>
          <div className="mb-4 flex items-center gap-2">
            <span className="rounded-full bg-black/25 px-3 py-1 text-[10.5px] font-semibold uppercase tracking-[0.08em] text-white/85 backdrop-blur">
              {template.is_official ? 'Featured' : 'Community'}
            </span>
          </div>
          <h3 className="max-w-[520px] text-[26px] font-semibold leading-[1.2] tracking-tight text-white sm:text-[30px]">
            {template.title}
          </h3>
        </div>
        <div className="mt-6 flex items-end justify-between gap-4">
          <IntegrationStrip integrations={shown} overflow={overflow} onDark />
          <CreatorPip creator={template.creator} isOfficial={template.is_official} onDark />
        </div>
      </div>

      <div className="relative z-10 hidden w-[38%] shrink-0 items-center justify-center p-4 sm:flex">
        <div className="relative aspect-video w-full overflow-hidden rounded-[12px] border border-white/12 bg-black/40 shadow-[0_20px_60px_-24px_rgba(0,0,0,0.6)] backdrop-blur">
          {template.graph?.nodes?.length ? (
            <TemplateGraphPreview graph={template.graph} static />
          ) : (
            <div className="flex h-full items-center justify-center text-[11px] text-white/40">
              No preview
            </div>
          )}
        </div>
      </div>
    </button>
  )
}

// ── Shared bits ──────────────────────────────────────────────────

function IntegrationStrip({
  integrations,
  overflow,
  onDark,
}: {
  integrations: string[]
  overflow: number
  onDark?: boolean
}) {
  const tileCls = onDark
    ? 'flex h-[34px] w-[34px] items-center justify-center overflow-hidden rounded-[8px] border border-white/12 bg-black/30 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)] [&_img]:h-5 [&_img]:w-5 [&_img]:object-contain'
    : 'flex h-[34px] w-[34px] items-center justify-center overflow-hidden rounded-[8px] bg-[var(--bg)] shadow-[inset_0_0_0_1px_var(--border-faint)] [&_img]:h-5 [&_img]:w-5 [&_img]:object-contain'
  const overflowCls = onDark
    ? 'flex h-[34px] min-w-[42px] items-center justify-center rounded-[8px] border border-white/12 bg-black/30 px-2.5 text-[12px] font-semibold text-white/75'
    : 'flex h-[34px] min-w-[42px] items-center justify-center rounded-[8px] bg-[var(--bg)] px-2.5 text-[12px] font-semibold text-[var(--text-mute)] shadow-[inset_0_0_0_1px_var(--border-faint)]'
  return (
    <div className="flex items-center gap-2">
      {integrations.map((slug) => (
        <span key={slug} className={tileCls} title={slug}>
          <BrandIcon slug={slug} />
        </span>
      ))}
      {overflow > 0 && <span className={overflowCls}>+{overflow}</span>}
    </div>
  )
}

function CreatorPip({
  creator,
  isOfficial,
  onDark,
}: {
  creator: TemplateListItem['creator']
  isOfficial: boolean
  onDark?: boolean
}) {
  const label = creator?.full_name || creator?.email?.split('@')[0] || (isOfficial ? 'Official' : 'Community')
  const initial = (label ?? '?').trim().charAt(0).toUpperCase()
  const ringCls = onDark ? 'border-white/15 bg-white/[0.08] text-white/85' : 'border-[var(--border-faint)] bg-[var(--bg)] text-[var(--text-mute)]'
  return (
    <div className="relative shrink-0" title={label ?? ''}>
      <span className={`flex h-10 w-10 items-center justify-center overflow-hidden rounded-full border text-[13px] font-semibold ${ringCls}`}>
        {creator?.avatar_url ? (
          <img src={creator.avatar_url} alt={label ?? ''} className="h-full w-full object-cover" />
        ) : (
          initial
        )}
      </span>
      {isOfficial && (
        <BadgeCheck
          className={`absolute -bottom-0.5 -right-0.5 h-[16px] w-[16px] rounded-full ${onDark ? 'bg-black text-white' : 'bg-[var(--bg-2)] text-[var(--accent)]'}`}
        />
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
