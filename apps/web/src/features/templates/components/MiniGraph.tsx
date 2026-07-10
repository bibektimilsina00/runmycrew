import { cloneElement, isValidElement, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { editorAPI } from '@/features/workflow-editor/services/editorAPI'
import { getIcon } from '@/features/workflow-editor/utils/icon-map'
import type { TemplateGraph } from '../types/templatesTypes'

/**
 * Lightweight workflow thumbnail: SVG bezier edges + absolutely
 * positioned icon chips, laid out from the graph's stored node
 * positions. Renders ~free compared to mounting ReactFlow per card,
 * and we control the look completely (no muddy canvas behind type).
 *
 * Coordinates are normalized to 0–100 on both axes and the SVG uses
 * `preserveAspectRatio="none"`, so curves stretch slightly with the
 * container's aspect ratio — invisible at thumbnail size.
 */

interface MiniGraphProps {
  graph: TemplateGraph
  /** Chip size in px. Featured cards can pass a bigger one. */
  chipSize?: number
}

interface LaidOutNode {
  id: string
  type: string
  x: number // 0–100
  y: number // 0–100
}

const PAD = 13 // % padding so chips never clip the container edge

function useNodeIconMap() {
  const { data } = useQuery({
    queryKey: ['node-definitions'],
    queryFn: ({ signal }) => editorAPI.getNodeDefinitions(signal),
    staleTime: 1000 * 60 * 10,
  })
  return useMemo(() => {
    if (!data) return null // defs not loaded yet — don't guess icon slugs
    const map = new Map<string, { icon: string; color?: string }>()
    for (const d of data) map.set(d.type, { icon: d.icon, color: d.color })
    return map
  }, [data])
}

function layoutNodes(graph: TemplateGraph): LaidOutNode[] {
  const nodes = graph?.nodes ?? []
  if (nodes.length === 0) return []

  const xs = nodes.map((n) => n.position?.x ?? 0)
  const ys = nodes.map((n) => n.position?.y ?? 0)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const spanX = maxX - minX
  const spanY = maxY - minY

  // Graphs saved without meaningful positions (everything stacked at
  // one point): fall back to a horizontal chain with a slight stagger.
  if (spanX < 1 && spanY < 1) {
    return nodes.map((n, i) => ({
      id: n.id,
      type: n.type ?? '',
      x: nodes.length === 1 ? 50 : PAD + (i * (100 - 2 * PAD)) / (nodes.length - 1),
      y: 50 + (i % 2 === 0 ? -8 : 8) * (nodes.length > 1 ? 1 : 0),
    }))
  }

  const scale = (v: number, min: number, span: number) =>
    span < 1 ? 50 : PAD + ((v - min) / span) * (100 - 2 * PAD)

  return nodes.map((n) => ({
    id: n.id,
    type: n.type ?? '',
    x: scale(n.position?.x ?? 0, minX, spanX),
    y: scale(n.position?.y ?? 0, minY, spanY),
  }))
}

function edgePath(a: LaidOutNode, b: LaidOutNode): string {
  const dx = Math.max(Math.abs(b.x - a.x) * 0.5, 10)
  return `M ${a.x} ${a.y} C ${a.x + dx} ${a.y}, ${b.x - dx} ${b.y}, ${b.x} ${b.y}`
}

export function MiniGraph({ graph, chipSize }: MiniGraphProps) {
  const iconByType = useNodeIconMap()
  const nodes = useMemo(() => layoutNodes(graph), [graph])
  const byId = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes])
  // Entry points: nodes nothing flows into. They get the accent ring so
  // the card telegraphs where the workflow starts.
  const targets = useMemo(
    () => new Set((graph?.edges ?? []).map((e) => e.target)),
    [graph],
  )

  if (nodes.length === 0) return null

  const size = chipSize ?? (nodes.length > 8 ? 28 : 34)

  return (
    <div className="absolute inset-0">
      <svg
        className="absolute inset-0 h-full w-full"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        {(graph?.edges ?? []).map((e, i) => {
          const a = byId.get(e.source)
          const b = byId.get(e.target)
          if (!a || !b) return null
          return (
            <path
              key={e.id ?? i}
              d={edgePath(a, b)}
              fill="none"
              stroke="var(--border-soft)"
              strokeWidth={1.5}
              vectorEffect="non-scaling-stroke"
              className="motion-safe:group-hover:[stroke:var(--accent-line)] motion-safe:group-hover:[stroke-dasharray:5_5] motion-safe:group-hover:animate-[template-edge-flow_0.6s_linear_infinite]"
            />
          )
        })}
      </svg>

      {nodes.map((n) => {
        const def = iconByType?.get(n.type)
        const icon = iconByType ? getIcon(def?.icon ?? n.type.split('.').pop() ?? '?') : null
        const iconSize = size - 14
        const isEntry = !targets.has(n.id)
        return (
          <span
            key={n.id}
            style={{ left: `${n.x}%`, top: `${n.y}%`, width: size, height: size, color: def?.color }}
            className={`absolute flex -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[9px] border bg-[var(--surface-2)] text-[var(--text-mute)] shadow-[0_2px_8px_-2px_rgba(0,0,0,0.5)] ${
              isEntry
                ? 'border-[var(--accent-line)] shadow-[0_0_12px_-2px_var(--accent-soft),0_2px_8px_-2px_rgba(0,0,0,0.5)]'
                : 'border-[var(--border-faint)]'
            }`}
            title={n.type}
          >
            {isValidElement<{ style?: React.CSSProperties }>(icon)
              ? cloneElement(icon, { style: { width: iconSize, height: iconSize } })
              : icon}
          </span>
        )
      })}
    </div>
  )
}
