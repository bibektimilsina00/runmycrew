import { ArrowUpRight, BadgeCheck, Download } from 'lucide-react'
import { MiniGraph } from './MiniGraph'
import { cn } from '@/lib/cn'
import type { TemplateListItem } from '../types/templatesTypes'

interface Props {
  template: TemplateListItem
  onClick?: () => void
  /** Wide hero tile: spans two grid columns, shorter preview, shows the summary. */
  featured?: boolean
}

/**
 * Template card with a real workflow preview as the hero: the graph's
 * own node layout rendered as icon chips + bezier edges on a dot-grid
 * canvas (see MiniGraph). Text lives below on a solid surface — never
 * on top of the preview — so nothing reads muddy. On hover the edges
 * animate a dash-flow, as if the workflow were running.
 */
export function TemplateCard({ template: t, onClick, featured = false }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'group flex w-full cursor-pointer flex-col overflow-hidden rounded-[14px] border border-[var(--border-faint)] bg-[var(--surface)] text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--accent-line)] hover:shadow-[0_0_0_1px_var(--accent-soft),0_24px_48px_-24px_rgba(0,0,0,0.6)]',
        featured && 'sm:col-span-2',
      )}
    >
      {/* ── Preview ── */}
      <div
        className={cn(
          'relative w-full overflow-hidden border-b border-[var(--border-faint)] bg-[var(--bg)]',
          featured ? 'aspect-[16/6.5]' : 'aspect-[16/10]',
        )}
      >
        <div className="absolute inset-0 bg-[radial-gradient(var(--border-faint)_1px,transparent_1px)] [background-size:14px_14px]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_70%_at_50%_45%,var(--accent-soft),transparent_70%)] opacity-60 transition-opacity duration-300 group-hover:opacity-100" />
        <div className="absolute inset-0 transition-transform duration-300 motion-safe:group-hover:scale-[1.045]">
          <MiniGraph graph={t.graph} chipSize={featured ? 40 : undefined} />
        </div>
      </div>

      {/* ── Body ── */}
      <div className="flex flex-1 flex-col gap-2.5 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3
            className={cn(
              'line-clamp-2 font-semibold leading-snug tracking-tight text-[var(--text)]',
              featured ? 'text-[17px]' : 'text-[14.5px]',
            )}
          >
            {t.title}
          </h3>
          <ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-[var(--text-faint)] opacity-0 transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-[var(--text)] group-hover:opacity-100" />
        </div>

        {featured && t.summary && (
          <p className="line-clamp-2 max-w-[640px] text-[12.5px] leading-relaxed text-[var(--text-mute)]">
            {t.summary}
          </p>
        )}

        <div className="mt-auto flex items-center gap-2 text-[11.5px] text-[var(--text-mute)]">
          <span className="rounded-full border border-[var(--border-faint)] bg-[var(--bg)] px-2 py-0.5 text-[10.5px] font-medium text-[var(--text-mute)]">
            {humanCategory(t.category)}
          </span>
          {t.steps > 0 && (
            <span className="text-[var(--text-faint)]">
              {t.steps} {t.steps === 1 ? 'step' : 'steps'}
            </span>
          )}
          <span className="flex items-center gap-1 text-[var(--text-faint)]">
            <Download className="h-3 w-3" />
            {t.download_count.toLocaleString()}
          </span>
          <span className="ml-auto flex items-center gap-1.5 truncate">
            <CreatorAvatar t={t} />
            {t.is_official && <BadgeCheck className="h-3.5 w-3.5 shrink-0 text-[var(--accent)]" />}
          </span>
        </div>
      </div>
    </button>
  )
}

function CreatorAvatar({ t }: { t: TemplateListItem }) {
  const label =
    t.creator?.full_name || t.creator?.email?.split('@')[0] || (t.is_official ? 'Official' : 'Community')
  const initial = label.trim().charAt(0).toUpperCase() || '?'
  return (
    <>
      <span className="flex h-5 w-5 shrink-0 items-center justify-center overflow-hidden rounded-full border border-[var(--border-faint)] bg-[var(--bg)] text-[9.5px] font-semibold text-[var(--text-mute)]">
        {t.creator?.avatar_url ? (
          <img src={t.creator.avatar_url} alt={label} className="h-full w-full object-cover" />
        ) : (
          initial
        )}
      </span>
      <span className="truncate text-[var(--text-faint)]">{label}</span>
    </>
  )
}

function humanCategory(c: string): string {
  return c.split('-').map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')
}
