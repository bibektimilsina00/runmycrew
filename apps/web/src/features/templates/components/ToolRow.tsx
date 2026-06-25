import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { editorAPI } from '@/features/workflow-editor/services/editorAPI'
import { getIcon } from '@/features/workflow-editor/utils/icon-map'
import type { NodeDefinition } from '@/features/workflow-editor/types/editorTypes'

/**
 * Compact row for the "Tools used" section. Mirrors `IntegrationRow`
 * shape but reads from the node-definitions catalog so the icon +
 * display name match what the editor renders for that node type.
 */

interface ToolRowProps {
  toolId: string
}

export function ToolRow({ toolId }: ToolRowProps) {
  const { data: definitions = [] } = useQuery({
    queryKey: ['node-definitions'],
    queryFn: ({ signal }) => editorAPI.getNodeDefinitions(signal),
    staleTime: 1000 * 60 * 10,
  })

  // Tool ids in templates are bare strings ("agent", "slack",
  // "github"); the catalog stores fully-qualified types like
  // "action.slack". Match both forms so seeded templates and
  // user-published ones both resolve.
  const def = useMemo<NodeDefinition | null>(() => {
    const lower = toolId.toLowerCase()
    return (
      definitions.find(
        (d) =>
          d.type.toLowerCase() === lower ||
          d.type.toLowerCase() === `action.${lower}` ||
          d.type.toLowerCase() === `ai.${lower}`,
      ) ?? null
    )
  }, [definitions, toolId])

  const displayName = def?.name ?? toolId
  const description = def?.description ?? def?.category ?? ''
  const colour = def?.color ?? 'var(--accent)'

  return (
    <div className="flex items-center gap-3.5 rounded-[10px] border border-[var(--border-faint)] bg-[var(--surface)] p-4">
      <div
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[8px] text-white shadow-[0_4px_10px_-4px_oklch(0_0_0/0.45)] [&_svg]:h-5 [&_svg]:w-5 [&_img]:h-5 [&_img]:w-5 [&_img]:object-contain"
        style={{ background: colour }}
      >
        {def ? getIcon(def.icon) : null}
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="truncate text-[14.5px] font-semibold text-[var(--text)] tracking-[-0.005em]">
          {displayName}
        </span>
        {description && (
          <span className="truncate text-[12.5px] text-[var(--text-mute)]">{description}</span>
        )}
      </div>

      {def?.type && (
        <span className="shrink-0 font-mono text-[10.5px] uppercase tracking-[0.06em] text-[var(--text-faint)]">
          {def.type}
        </span>
      )}
    </div>
  )
}
