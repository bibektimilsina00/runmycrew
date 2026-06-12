import { useMemo, useState } from 'react'
import { ChevronDown, Copy, Check } from 'lucide-react'
import type { Node, Edge } from 'reactflow'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'
import { getIcon } from '../../../utils/icon-map'
import { JsonTreeView } from '../../right-panel/panels/logs/JsonTreeView'
import type { NodeDefinition } from '../../../types/editorTypes'

interface UpstreamConnectionsSectionProps {
  nodeId: string
}

interface Ancestor {
  node: Node
  definition: NodeDefinition | null
  distance: number
}

/**
 * BFS over reverse edges from `start`. Records each ancestor at its shortest
 * distance; the visited set guards against cycles and avoids re-queueing nodes
 * reachable through multiple paths.
 */
function collectAncestors(start: string, edges: Edge[]): Map<string, number> {
  const parentsOf = new Map<string, string[]>()
  for (const e of edges) {
    const list = parentsOf.get(e.target)
    if (list) list.push(e.source)
    else parentsOf.set(e.target, [e.source])
  }
  const distance = new Map<string, number>()
  const queue: Array<[string, number]> = [[start, 0]]
  while (queue.length) {
    const [id, d] = queue.shift()!
    for (const src of parentsOf.get(id) ?? []) {
      if (distance.has(src) || src === start) continue
      distance.set(src, d + 1)
      queue.push([src, d + 1])
    }
  }
  return distance
}

/**
 * Renders every upstream node (transitive predecessors) of the selected node,
 * ordered closest-first. Each row is collapsible — when expanded it shows the
 * ancestor's last successful run output as a draggable JSON tree, falling back
 * to the static output schema when no run data exists.
 */
export function UpstreamConnectionsSection({ nodeId }: UpstreamConnectionsSectionProps) {
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const edges = useWorkflowEditorStore(s => s.edges)
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)

  const ancestors = useMemo<Ancestor[]>(() => {
    const distance = collectAncestors(nodeId, edges)
    const list: Ancestor[] = []
    for (const [id, d] of distance) {
      const node = nodes.find(n => n.id === id)
      if (!node) continue
      const definition = nodeDefinitions.find(def => def.type === node.type) ?? null
      list.push({ node, definition, distance: d })
    }
    list.sort((a, b) => a.distance - b.distance)
    return list
  }, [nodeId, nodes, edges, nodeDefinitions])

  return (
    <div className="shrink-0 border-t border-[var(--border-faint)]">
      <div className="flex h-10 items-center justify-between px-4">
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--text-mute)]">
          Inputs
        </span>
        <span className="font-mono text-[10px] text-[var(--text-dim)]">{ancestors.length}</span>
      </div>
      {ancestors.length === 0 ? (
        <p className="px-4 pb-3 text-[11.5px] italic text-[var(--text-faint)]">
          No upstream nodes connected.
        </p>
      ) : (
        <div className="flex flex-col gap-1 px-3 pb-3">
          {ancestors.map(a => (
            <AncestorRow key={a.node.id} ancestor={a} />
          ))}
        </div>
      )}
    </div>
  )
}

function AncestorRow({ ancestor }: { ancestor: Ancestor }) {
  const [open, setOpen] = useState(false)
  const { node, definition, distance } = ancestor
  const run = useWorkflowEditorStore(s => s.nodeRuns[node.id])

  const Icon = definition ? getIcon(definition.icon) : null
  const label = (node.data?.label as string | undefined) || definition?.name || node.id
  const hasOutput = run?.status === 'success' && run.output !== undefined

  return (
    <div className="overflow-hidden rounded-[7px] border border-[var(--border-faint)] bg-[var(--bg)]">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="flex w-full items-center gap-2 px-2.5 py-1.5 text-left transition-colors hover:bg-[var(--surface)]"
      >
        {definition && (
          <div
            className="flex h-5 w-5 shrink-0 items-center justify-center rounded-[5px] text-white [&_svg]:h-3 [&_svg]:w-3"
            style={{ background: definition.color ?? 'var(--surface-3)' }}
          >
            {Icon}
          </div>
        )}
        <span className="min-w-0 flex-1 truncate text-[12px] text-[var(--text)]">{label}</span>
        <span className="font-mono text-[10px] text-[var(--text-dim)]">
          {distance === 1 ? 'direct' : `${distance} hops`}
        </span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 text-[var(--text-faint)] transition-transform duration-150',
            open && 'rotate-180',
          )}
        />
      </button>
      {open && (
        <div className="border-t border-[var(--border-faint)] bg-[var(--bg-2)] px-3 py-2">
          {hasOutput ? (
            <JsonTreeView value={run.output} nodeId={node.id} initialDepth={1} />
          ) : (
            <SchemaList nodeId={node.id} outputs={definition?.outputsSchema ?? []} />
          )}
        </div>
      )}
    </div>
  )
}

const typeClass: Record<string, string> = {
  string:  'text-[var(--ok)]',
  number:  'text-[var(--accent)]',
  boolean: 'text-[var(--warn)]',
  object:  'text-[var(--text-mute)]',
  array:   'text-[var(--text-mute)]',
}

function SchemaList({ nodeId, outputs }: { nodeId: string; outputs: { label: string; type: string }[] }) {
  const [copied, setCopied] = useState<string | null>(null)

  if (outputs.length === 0) {
    return (
      <p className="text-[11px] italic text-[var(--text-faint)]">
        No run output yet — schema unavailable.
      </p>
    )
  }

  const copyValue = async (label: string) => {
    await navigator.clipboard.writeText(`{{${nodeId}.${label}}}`)
    setCopied(label)
    setTimeout(() => setCopied(null), 1200)
  }

  return (
    <div className="flex flex-col gap-0.5">
      {outputs.map(output => (
        <button
          key={output.label}
          type="button"
          onClick={() => void copyValue(output.label)}
          className="group flex h-7 items-center gap-2 rounded-[6px] px-1.5 text-left transition-colors hover:bg-[var(--surface)]"
          title={`Copy {{${nodeId}.${output.label}}}`}
        >
          <span className="min-w-0 flex-1 truncate font-mono text-[11px] text-[var(--text)]">
            {output.label}
          </span>
          <span className={cn('font-mono text-[10px]', typeClass[output.type] ?? 'text-[var(--text-faint)]')}>
            {output.type}
          </span>
          {copied === output.label
            ? <Check className="h-3 w-3 text-[var(--ok)]" />
            : <Copy className="h-3 w-3 text-[var(--text-faint)] opacity-0 transition-opacity group-hover:opacity-100" />
          }
        </button>
      ))}
      <p className="mt-0.5 px-1.5 text-[10px] italic text-[var(--text-dim)]">
        Click to copy interpolation. Run the upstream node to see its actual output here.
      </p>
    </div>
  )
}
