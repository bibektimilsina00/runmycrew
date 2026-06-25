import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { editorAPI } from '@/features/workflow-editor/services/editorAPI'
import { getIcon } from '@/features/workflow-editor/utils/icon-map'
import type { NodeDefinition } from '@/features/workflow-editor/types/editorTypes'
import { useCredentials } from '@/features/connections/hooks/useConnections'
import type { TemplateDetail } from '../types/templatesTypes'
import { IntegrationRow } from './IntegrationRow'
import { ToolRow } from './ToolRow'
import { TemplateGraphPreview } from './TemplateGraphPreview'

/**
 * Stacked content sections for the main column.
 *
 * Replaces the previous Tabs UI — the user prefers a single scrollable
 * page with every section visible. Order: Overview → Workflow (graph
 * + node list) → Requirements (integrations + tools + missing-creds
 * alert) → Instructions.
 *
 * Component name kept as `DetailTabs` so existing imports don't churn.
 */

interface DetailTabsProps {
  template: TemplateDetail
  missingCredentials: string[]
}

export function DetailTabs({ template }: DetailTabsProps) {
  // Per-row connection status replaces the old "missing-creds" banner —
  // each integration shows Connected ✓ or a Connect button. Banner gone.
  const { data: credentials = [] } = useCredentials()
  return (
    <div className="flex flex-col gap-[40px]">
      <section className="flex flex-col gap-4">
        <SectionHeading>Overview</SectionHeading>
        {template.summary && (
          <p className="m-0 text-[15px] leading-[1.6] font-medium text-[var(--text)]">
            {template.summary}
          </p>
        )}
        <p className="m-0 whitespace-pre-wrap text-[14px] leading-[1.7] text-[var(--text-mute)]">
          {template.description || 'No long-form description provided yet.'}
        </p>
      </section>

      <Divider />

      <section className="flex flex-col gap-4">
        <SectionHeading>Workflow graph</SectionHeading>
        <div className="relative aspect-[2/1] w-full overflow-hidden rounded-[10px] border border-[var(--border-faint)] bg-[var(--bg)]">
          {template.graph?.nodes?.length ? (
            <TemplateGraphPreview graph={template.graph} />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-[12px] text-[var(--text-faint)]">
              No graph data
            </div>
          )}
        </div>
        <NodeList template={template} />
      </section>

      <Divider />

      <section className="flex flex-col gap-4">
        <SectionHeading>Integrations required</SectionHeading>
        {template.credentials_required.length === 0 ? (
          <span className="text-[13.5px] italic text-[var(--text-faint)]">
            No integrations required.
          </span>
        ) : (
          <div className="flex flex-col gap-2.5">
            {template.credentials_required.map((c) => (
              <IntegrationRow key={c} required={c} connected={credentials} />
            ))}
          </div>
        )}
      </section>

      <Divider />

      <section className="flex flex-col gap-4">
        <SectionHeading>Tools used</SectionHeading>
        {template.tools_required.length === 0 ? (
          <span className="text-[13.5px] italic text-[var(--text-faint)]">
            No tools used.
          </span>
        ) : (
          <div className="flex flex-col gap-2.5">
            {template.tools_required.map((t) => (
              <ToolRow key={t} toolId={t} />
            ))}
          </div>
        )}
      </section>

      <Divider />

      <section className="flex flex-col gap-4">
        <SectionHeading>Getting started</SectionHeading>
        <ol className="m-0 flex flex-col gap-2.5 pl-4 text-[14px] leading-[1.7] text-[var(--text-mute)]">
          <li>
            Click <span className="font-semibold text-[var(--text)]">Use template</span> to add
            it as a new workflow in your workspace.
          </li>
          {template.credentials_required.length > 0 && (
            <li>
              Connect the required integrations in{' '}
              <span className="font-semibold text-[var(--text)]">Settings → Connections</span>{' '}
              so the workflow's tool calls can authenticate.
            </li>
          )}
          <li>
            Open the workflow editor, review the nodes, and tweak any property defaults to suit
            your data shape.
          </li>
          <li>
            Hit <span className="font-semibold text-[var(--text)]">Activate</span> in the editor
            topbar to enable triggers.
          </li>
        </ol>
      </section>
    </div>
  )
}

function SectionHeading({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  // Matches the marketplace + dashboard heading scale — 18px semibold
  // with the same tracking the h1 uses so detail sections read as part
  // of the same vocabulary.
  return (
    <h2
      className={`m-0 text-[18px] font-semibold tracking-[-0.014em] text-[var(--text)] ${className ?? ''}`.trim()}
    >
      {children}
    </h2>
  )
}

function Divider() {
  return <div className="h-px bg-[var(--border-faint)]" />
}

function NodeList({ template }: { template: TemplateDetail }) {
  const { data: definitions = [] } = useQuery({
    queryKey: ['node-definitions'],
    queryFn: ({ signal }) => editorAPI.getNodeDefinitions(signal),
    staleTime: 1000 * 60 * 10,
  })

  const defByType = useMemo(() => {
    const map = new Map<string, NodeDefinition>()
    for (const d of definitions) map.set(d.type, d)
    return map
  }, [definitions])

  const nodes = template.graph?.nodes ?? []
  if (nodes.length === 0) return null

  return (
    <div className="flex flex-col gap-2.5">
      <SectionHeading>Nodes ({nodes.length})</SectionHeading>
      <div className="flex flex-col divide-y divide-[var(--border-faint)] rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)]">
        {nodes.map((n, idx) => {
          const def = defByType.get(n.type ?? '')
          const colour = def?.color ?? '#5e6ad2'
          return (
            <div key={n.id ?? idx} className="flex items-center gap-3 px-4 py-3">
              <div
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[7px] text-white [&_svg]:h-4 [&_svg]:w-4 [&_img]:h-4 [&_img]:w-4 [&_img]:object-contain"
                style={{ background: colour }}
              >
                {def ? getIcon(def.icon) : null}
              </div>
              <div className="flex min-w-0 flex-col">
                <span className="truncate text-[13.5px] font-medium text-[var(--text)]">
                  {def?.name ?? n.type ?? 'Node'}
                </span>
                <span className="truncate font-mono text-[11px] uppercase tracking-[0.06em] text-[var(--text-faint)]">
                  {n.type}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
