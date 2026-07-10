import { BadgeCheck, Bot } from 'lucide-react'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'
import type { TemplateListItem } from '../types/templatesTypes'

interface Props {
  template: TemplateListItem
  onClick?: () => void
  /** Featured / hero variant — larger padding, coloured backdrop, big preview slot. */
  variant?: 'grid' | 'featured'
}

/**
 * n8n workflows-page card. Title dominates. Bottom row = integration
 * icon strip + "+N" overflow chip. Creator avatar floats at the
 * bottom-right with a small verified pip. No summary text (matches n8n
 * — the title carries the meaning).
 */
export function TemplateCard({ template, onClick, variant = 'grid' }: Props) {
  const integrations = deriveIntegrations(template)
  const overflow = Math.max(0, integrations.length - 3)
  const shown = integrations.slice(0, 3)
  const bg = template.bg_variant || 'inspo-bg-1'

  if (variant === 'featured') {
    return (
      <button
        type="button"
        onClick={onClick}
        className={`group relative flex w-full items-center overflow-hidden rounded-[16px] border border-border-faint text-left transition-transform hover:-translate-y-0.5 ${bg}`}
      >
        {/* Text side */}
        <div className="relative z-10 flex-1 px-8 py-8">
          <div className="mb-4 flex items-center gap-2 text-[10.5px] font-semibold uppercase tracking-wider text-white/70">
            {template.is_official && <span className="rounded-full bg-white/15 px-2 py-0.5">Featured</span>}
          </div>
          <h3 className="max-w-[520px] text-[24px] font-semibold leading-tight tracking-tight text-white">
            {template.title}
          </h3>
          <div className="mt-6 flex items-center gap-2">
            <IntegrationStrip integrations={shown} overflow={overflow} onDark />
          </div>
        </div>
        {/* Preview side — muted mini-graph illustration */}
        <div className="relative z-10 mr-8 hidden h-[160px] w-[280px] items-center justify-center rounded-[10px] bg-black/25 backdrop-blur sm:flex">
          <Bot className="h-14 w-14 text-white/60" />
        </div>
        {/* Creator pip */}
        <CreatorPip creator={template.creator} isOfficial={template.is_official} />
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="group relative flex h-[172px] w-full flex-col justify-between overflow-hidden rounded-[14px] border border-border-faint bg-bg2 p-5 text-left transition-all hover:-translate-y-0.5 hover:border-border hover:bg-bg2/80"
    >
      <h3 className="line-clamp-3 pr-8 text-[15.5px] font-semibold leading-snug text-text">
        {template.title}
      </h3>

      <div className="flex items-end justify-between gap-3">
        <IntegrationStrip integrations={shown} overflow={overflow} />
        <CreatorPip creator={template.creator} isOfficial={template.is_official} />
      </div>
    </button>
  )
}

// ── Bits ─────────────────────────────────────────────────────────

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
    ? 'flex h-8 w-8 items-center justify-center overflow-hidden rounded-[7px] bg-black/40 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.08)] [&_img]:h-5 [&_img]:w-5 [&_img]:object-contain'
    : 'flex h-8 w-8 items-center justify-center overflow-hidden rounded-[7px] bg-white/[0.04] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)] [&_img]:h-5 [&_img]:w-5 [&_img]:object-contain'
  const overflowCls = onDark
    ? 'flex h-8 min-w-[36px] items-center justify-center rounded-[7px] bg-black/40 px-2 text-[11.5px] font-semibold text-white/70'
    : 'flex h-8 min-w-[36px] items-center justify-center rounded-[7px] bg-white/[0.04] px-2 text-[11.5px] font-semibold text-text-mute'
  return (
    <div className="flex items-center gap-1.5">
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
}: {
  creator: TemplateListItem['creator']
  isOfficial: boolean
}) {
  const label = creator?.full_name || creator?.email?.split('@')[0] || (isOfficial ? 'Official' : 'Community')
  const initial = (label ?? '?').trim().charAt(0).toUpperCase()
  return (
    <div className="relative shrink-0" title={label ?? ''}>
      <span className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border border-border-faint bg-surface text-[12px] font-semibold text-text-mute">
        {creator?.avatar_url ? (
          <img src={creator.avatar_url} alt={label ?? ''} className="h-full w-full object-cover" />
        ) : (
          initial
        )}
      </span>
      {isOfficial && (
        <BadgeCheck className="absolute -bottom-0.5 -right-0.5 h-4 w-4 rounded-full bg-bg2 text-accent" />
      )}
    </div>
  )
}

// ── Helpers ─────────────────────────────────────────────────────

const TRIGGER_TYPES = new Set([
  'chat_app', 'manual', 'cron', 'webhook', 'trigger',
  'set_variable', 'merge', 'switch', 'condition', 'delay', 'wait',
  'json_transform', 'code', 'sub_workflow',
])

function deriveIntegrations(t: TemplateListItem): string[] {
  const s = new Set<string>()
  for (const id of t.tools_required ?? []) s.add(id.toLowerCase())
  for (const node of t.graph?.nodes ?? []) {
    const type = node.type ?? ''
    const brand = type.split('.').pop()
    if (brand && !TRIGGER_TYPES.has(brand)) s.add(brand.toLowerCase())
  }
  return Array.from(s)
}
