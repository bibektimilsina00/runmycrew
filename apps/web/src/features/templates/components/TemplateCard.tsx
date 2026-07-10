import { BadgeCheck, Bolt } from 'lucide-react'
import { CreatorChip } from './CreatorChip'
import { PremiumBadge } from './PremiumBadge'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'
import { TEMPLATE_CATEGORIES } from '../types/templatesTypes'
import type { TemplateListItem } from '../types/templatesTypes'

interface Props {
  template: TemplateListItem
  onClick?: () => void
}

/**
 * n8n-style template card. Header strip is the theme colour (from
 * bg_variant → subtle radial gradient); below it we lay out title,
 * summary, integration icons row, and creator + install count.
 * Hover lifts the card + darkens the border for tactile feedback.
 */
export function TemplateCard({ template, onClick }: Props) {
  const integrations = deriveIntegrations(template)
  const categoryLabel =
    TEMPLATE_CATEGORIES.find((c) => c.id === template.category)?.label ?? template.category

  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex h-full flex-col overflow-hidden rounded-[14px] border border-border-faint bg-bg2 text-left transition-all hover:-translate-y-0.5 hover:border-border hover:shadow-[0_18px_36px_-24px_rgba(0,0,0,0.5)]"
    >
      {/* Colored header strip — subtle gradient so it never overwhelms
          the content but still gives the card a personality. */}
      <div
        className={`relative h-[86px] w-full overflow-hidden ${template.bg_variant}`}
      >
        {template.is_premium && (template.price_cents ?? 0) > 0 ? (
          <PremiumBadge priceCents={template.price_cents ?? 0} />
        ) : (
          <span className="absolute right-3 top-3 rounded-[6px] border border-white/15 bg-black/25 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-white/85 backdrop-blur">
            Free
          </span>
        )}
        <div className="absolute bottom-3 left-4 flex items-center gap-1.5 rounded-[6px] bg-black/35 px-2 py-0.5 text-[10.5px] font-medium uppercase tracking-wider text-white/85 backdrop-blur">
          {categoryLabel}
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 flex-col gap-3 px-4 py-4">
        <div className="flex-1">
          <h3 className="line-clamp-2 text-[14.5px] font-semibold leading-snug text-text">
            {template.title}
          </h3>
          {template.summary && (
            <p className="mt-1.5 line-clamp-2 text-[12.5px] leading-relaxed text-text-mute">
              {template.summary}
            </p>
          )}
        </div>

        {/* Integrations */}
        {integrations.length > 0 && (
          <div className="flex items-center gap-1">
            {integrations.slice(0, 6).map((slug) => (
              <span
                key={slug}
                className="flex h-6 w-6 items-center justify-center overflow-hidden rounded-[6px] bg-white shadow-[inset_0_0_0_1px_rgba(0,0,0,0.06)] [&_img]:h-4 [&_img]:w-4 [&_img]:object-contain"
                title={slug}
              >
                <BrandIcon slug={slug} />
              </span>
            ))}
            {integrations.length > 6 && (
              <span className="ml-1 text-[10.5px] text-text-faint">
                +{integrations.length - 6}
              </span>
            )}
          </div>
        )}

        {/* Footer meta */}
        <div className="flex items-center justify-between gap-2 border-t border-border-faint pt-2.5 text-[11px] text-text-faint">
          {template.is_official ? (
            <span className="flex items-center gap-1 font-mono uppercase tracking-[0.06em] text-accent">
              <BadgeCheck className="h-[12px] w-[12px]" />
              Official
            </span>
          ) : template.creator ? (
            <CreatorChip creator={template.creator} />
          ) : (
            <span className="font-mono uppercase tracking-[0.06em]">Community</span>
          )}
          <span className="flex items-center gap-1 tabular-nums">
            <Bolt className="h-[11px] w-[11px]" />
            {template.download_count.toLocaleString()}
          </span>
        </div>
      </div>
    </button>
  )
}

/**
 * Pulls brand slugs off the template. Backend already gives us
 * ``tools_required`` + ``credentials_required`` — merge + dedup.
 * Fallback to graph node types when both lists are empty.
 */
function deriveIntegrations(t: TemplateListItem): string[] {
  const s = new Set<string>()
  for (const id of t.tools_required ?? []) s.add(id.toLowerCase())
  for (const node of t.graph?.nodes ?? []) {
    const type = node.type ?? ''
    const brand = type.split('.').pop()
    if (brand && brand !== 'chat_app' && brand !== 'manual' && brand !== 'cron' && brand !== 'webhook') {
      s.add(brand.toLowerCase())
    }
  }
  return Array.from(s)
}
