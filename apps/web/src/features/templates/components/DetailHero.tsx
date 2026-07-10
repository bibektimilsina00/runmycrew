import { Download, GitBranch, Workflow as WorkflowIcon } from 'lucide-react'
import { MiniGraph } from './MiniGraph'
import type { TemplateDetail } from '../types/templatesTypes'

/**
 * Detail-page hero: eyebrow + h1 + summary, then a wide MiniGraph
 * render of the workflow — same visual language as the gallery cards
 * (icon chips + bezier edges on a dot grid), just bigger. Stats sit
 * in a quiet row under the preview instead of overlaying it.
 */

interface DetailHeroProps {
  template: TemplateDetail
}

export function DetailHero({ template }: DetailHeroProps) {
  const nodeCount = template.graph?.nodes?.length ?? template.steps ?? 0
  const edgeCount = template.graph?.edges?.length ?? 0

  return (
    <div className="flex flex-col gap-[18px]">
      <div className="flex items-center gap-[8px]">
        <span className="relative inline-flex w-[8px] h-[8px]">
          <span className="absolute inset-0 rounded-full bg-[var(--accent)]" />
        </span>
        <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--text-faint)] uppercase">
          {humanCategory(template.category)}
        </span>
        <span className="text-[var(--text-dim)]">·</span>
        <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--text-dim)] uppercase">
          {template.kind}
        </span>
        {template.is_official && (
          <>
            <span className="text-[var(--text-dim)]">·</span>
            <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--accent)] uppercase">
              Official
            </span>
          </>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <h1 className="m-0 text-[27px] font-semibold tracking-[-0.022em] text-[var(--text)]">
          {template.title}
        </h1>
        {template.summary && (
          <p className="m-0 max-w-[640px] text-[14px] leading-[1.55] text-[var(--text-mute)]">
            {template.summary}
          </p>
        )}
      </div>

      {/* Wide preview — gallery-card language at hero scale */}
      <div className="relative aspect-[21/9] w-full overflow-hidden rounded-[14px] border border-[var(--border-faint)] bg-[var(--bg)]">
        <div className="absolute inset-0 bg-[radial-gradient(var(--border-faint)_1px,transparent_1px)] [background-size:16px_16px]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_55%_65%_at_50%_45%,var(--accent-soft),transparent_70%)] opacity-70" />
        {nodeCount > 0 ? (
          <MiniGraph graph={template.graph} chipSize={46} />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-[12px] text-[var(--text-faint)]">
            No graph data
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-5 text-[12px] text-[var(--text-mute)]">
        <span className="flex items-center gap-1.5">
          <WorkflowIcon className="h-3.5 w-3.5 text-[var(--text-faint)]" />
          {nodeCount} {nodeCount === 1 ? 'node' : 'nodes'}
        </span>
        <span className="flex items-center gap-1.5">
          <GitBranch className="h-3.5 w-3.5 text-[var(--text-faint)]" />
          {edgeCount} {edgeCount === 1 ? 'connection' : 'connections'}
        </span>
        <span className="flex items-center gap-1.5">
          <Download className="h-3.5 w-3.5 text-[var(--text-faint)]" />
          {template.download_count.toLocaleString()} installs
        </span>
      </div>
    </div>
  )
}

function humanCategory(cat: string): string {
  return cat
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
}
