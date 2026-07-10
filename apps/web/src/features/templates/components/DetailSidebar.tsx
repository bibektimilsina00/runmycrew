import {
  Sparkles,
  Crown,
  CheckCircle2,
  Download,
  Calendar,
  Plug,
  FileDown,
  User as UserIcon,
  Rocket,
  Loader2,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { APP_ROUTES } from '@/shared/constants/routes'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'
import type { TemplateDetail } from '../types/templatesTypes'

interface DetailSidebarProps {
  template: TemplateDetail
  missingCredentials: string[]
  onInstall?: () => void
  installing?: boolean
}

/**
 * n8n-style right rail. Big install CTA up top, then a stack of small
 * info cards (integrations used, categories, creator, stats,
 * resources). Sticks below the sub-header on lg+ screens.
 */
export function DetailSidebar({
  template,
  missingCredentials,
  onInstall,
  installing,
}: DetailSidebarProps) {
  const navigate = useNavigate()
  const integrations = deriveIntegrations(template)

  return (
    <aside className="flex flex-col gap-[14px] lg:sticky lg:top-[80px]">
      {/* ── Install CTA ────────────────────────────────────── */}
      <Block className="items-stretch">
        <div className="flex items-baseline justify-between">
          <BlockTitle
            icon={
              template.is_premium ? (
                <Crown className="h-3.5 w-3.5" style={{ color: 'oklch(0.68 0.18 75)' }} />
              ) : (
                <Sparkles className="h-3.5 w-3.5" />
              )
            }
          >
            {template.is_premium ? 'Premium template' : 'Free template'}
          </BlockTitle>
          <span className="font-mono text-[18px] font-semibold tracking-tight text-text">
            {template.is_premium ? formatPrice(template.price_cents) : 'Free'}
          </span>
        </div>
        {onInstall && (
          <button
            onClick={onInstall}
            disabled={installing}
            className="mt-2 flex h-10 w-full items-center justify-center gap-2 rounded-[8px] text-[13.5px] font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            style={{ background: 'var(--accent, #8b5cf6)' }}
          >
            {installing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
            {template.is_premium ? 'Buy & install' : 'Use this template'}
          </button>
        )}
        {missingCredentials.length > 0 && (
          <div className="mt-1 text-[11.5px] text-warn">
            Missing {missingCredentials.length} connection{missingCredentials.length === 1 ? '' : 's'} — install still works, connect afterwards.
          </div>
        )}
      </Block>

      {/* ── Integrations used ─────────────────────────────── */}
      {integrations.length > 0 && (
        <Block>
          <BlockTitle icon={<Plug className="h-3.5 w-3.5" />}>Integrations used</BlockTitle>
          <div className="flex flex-col gap-1">
            {integrations.map(slug => (
              <div
                key={slug}
                className="flex items-center gap-2 rounded-[7px] px-1 py-1"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center overflow-hidden rounded-[6px] bg-white shadow-[inset_0_0_0_1px_rgba(0,0,0,0.06)] [&_img]:h-4 [&_img]:w-4 [&_img]:object-contain">
                  <BrandIcon slug={slug} />
                </span>
                <span className="truncate text-[12.5px] text-text">
                  {slug.replace(/[-_]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
              </div>
            ))}
          </div>
        </Block>
      )}

      {/* ── Categories ────────────────────────────────────── */}
      <Block>
        <BlockTitle>Categories</BlockTitle>
        <div className="flex flex-wrap gap-1.5">
          <Pill>{humanCategory(template.category)}</Pill>
          <Pill>{template.kind}</Pill>
        </div>
      </Block>

      {/* ── Creator ───────────────────────────────────────── */}
      {!template.is_official && template.creator && (
        <Block>
          <BlockTitle icon={<UserIcon className="h-3.5 w-3.5" />}>Created by</BlockTitle>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-[8px] bg-accent text-[14px] font-semibold text-white">
              {template.creator.avatar_url ? (
                <img
                  src={template.creator.avatar_url}
                  alt={template.creator.full_name ?? ''}
                  className="h-full w-full object-cover"
                />
              ) : (
                (template.creator.full_name ?? template.creator.email ?? '?').trim().charAt(0).toUpperCase()
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-[13px] font-semibold text-text">
                {template.creator.full_name?.trim() ||
                  template.creator.email?.split('@')[0] ||
                  'Anonymous'}
              </div>
              <div className="text-[10.5px] uppercase tracking-[0.06em] text-text-faint">
                Published {formatDate(template.created_at)}
              </div>
            </div>
          </div>
        </Block>
      )}
      {template.is_official && (
        <Block>
          <div className="flex items-center gap-2 text-[13px] text-text">
            <CheckCircle2 className="h-4 w-4 text-accent" />
            <span className="font-medium">Official template</span>
          </div>
          <div className="text-[11px] text-text-mute">
            Maintained by the RunMyCrew team.
          </div>
        </Block>
      )}

      {/* ── Stats ─────────────────────────────────────────── */}
      <Block>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <BlockTitle icon={<Download className="h-3.5 w-3.5" />}>Installs</BlockTitle>
            <span className="font-mono text-[18px] font-semibold text-text">
              {template.download_count.toLocaleString()}
            </span>
          </div>
          <div>
            <BlockTitle icon={<Calendar className="h-3.5 w-3.5" />}>Updated</BlockTitle>
            <span className="font-mono text-[12px] uppercase tracking-[0.06em] text-text-mute">
              {formatDate(template.updated_at)}
            </span>
          </div>
        </div>
      </Block>

      {/* ── Resources ─────────────────────────────────────── */}
      <Block>
        <BlockTitle>Resources</BlockTitle>
        <div className="flex flex-col gap-1">
          {missingCredentials.length > 0 && (
            <ResourceLink onClick={() => navigate(APP_ROUTES.CONNECTIONS)}>
              <Plug className="h-3.5 w-3.5 text-warn" />
              Connect {missingCredentials.length} required integration
              {missingCredentials.length === 1 ? '' : 's'}
            </ResourceLink>
          )}
          <ResourceLink onClick={exportJson(template.slug, template.graph)}>
            <FileDown className="h-3.5 w-3.5 text-text-mute" />
            Export workflow JSON
          </ResourceLink>
        </div>
      </Block>
    </aside>
  )
}

// ── Building blocks ──────────────────────────────────────────────

function Block({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`flex flex-col gap-2 rounded-[10px] border border-border-faint bg-surface p-[14px] ${className ?? ''}`}>
      {children}
    </div>
  )
}

function BlockTitle({ icon, children }: { icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <span className="flex items-center gap-1.5 text-[10.5px] font-bold uppercase tracking-[0.08em] text-text-dim">
      {icon}
      {children}
    </span>
  )
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-[6px] border border-border-faint bg-bg px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-text-mute">
      {children}
    </span>
  )
}

function ResourceLink({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-[6px] px-1 py-1.5 text-left text-[12.5px] text-text-mute transition-colors hover:bg-bg hover:text-text"
    >
      {children}
    </button>
  )
}

// ── Helpers ──────────────────────────────────────────────────────

function exportJson(slug: string, graph: unknown) {
  return () => {
    const blob = new Blob([JSON.stringify(graph, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${slug}.workflow.json`
    a.click()
    URL.revokeObjectURL(url)
  }
}

function formatPrice(cents: number): string {
  if (cents <= 0) return 'Free'
  const dollars = cents / 100
  return Number.isInteger(dollars) ? `$${dollars}` : `$${dollars.toFixed(2)}`
}

function humanCategory(cat: string): string {
  return cat
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function deriveIntegrations(t: TemplateDetail): string[] {
  const s = new Set<string>()
  for (const id of t.tools_required ?? []) s.add(id.toLowerCase())
  for (const id of t.credentials_required ?? []) s.add(id.toLowerCase())
  for (const node of t.graph?.nodes ?? []) {
    const type = node.type ?? ''
    const brand = type.split('.').pop()
    if (brand && !['chat_app', 'manual', 'cron', 'webhook', 'set_variable', 'merge', 'switch', 'condition', 'delay', 'wait', 'json_transform', 'code', 'trigger'].includes(brand)) {
      s.add(brand.toLowerCase())
    }
  }
  return Array.from(s).slice(0, 15)
}
