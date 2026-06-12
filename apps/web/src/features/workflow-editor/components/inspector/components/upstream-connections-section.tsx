import React, { useMemo, useState } from 'react'
import { ChevronDown } from 'lucide-react'
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
 * BFS over reverse edges. Records each ancestor at its shortest distance;
 * the visited set guards against cycles.
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
 * Builds a stub JSON value from `outputsSchema` so the tree view can render it
 * the same way it renders real output. Drag-drop still produces
 * `{{nodeId.label}}` because the tree row's path is the field label.
 */
function schemaToStub(outputs: { label: string; type: string }[]): Record<string, unknown> {
  const stub: Record<string, unknown> = {}
  for (const o of outputs) {
    switch (o.type) {
      case 'string':  stub[o.label] = ''; break
      case 'number':  stub[o.label] = 0; break
      case 'boolean': stub[o.label] = false; break
      case 'object':  stub[o.label] = {}; break
      case 'array':   stub[o.label] = []; break
      default:        stub[o.label] = null
    }
  }
  return stub
}

/**
 * Lists every upstream node (transitive predecessors) of the selected node,
 * ordered closest-first. Each row toggles expand to show the ancestor's real
 * run output as a draggable JsonTreeView, falling back to a stub built from
 * its outputsSchema so drag-drop still inserts `{{nodeId.path}}` even before
 * the node has been run.
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
    <div className="shrink-0 border-t border-[var(--border-faint)] px-3 py-3">
      <div className="mb-1.5 flex items-center justify-between px-1">
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--text-mute)]">
          Inputs
        </span>
        {ancestors.length > 0 && (
          <span className="font-mono text-[10px] text-[var(--text-dim)]">{ancestors.length}</span>
        )}
      </div>
      {ancestors.length === 0 ? (
        <p className="px-1 text-[11.5px] italic text-[var(--text-faint)]">
          No upstream nodes connected.
        </p>
      ) : (
        <div className="flex flex-col gap-0.5">
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

  const label = (node.data?.label as string | undefined) || definition?.name || node.id
  const hasOutput = run?.status === 'success' && run.output !== undefined
  const stub = useMemo(
    () => (hasOutput ? null : schemaToStub(definition?.outputsSchema ?? [])),
    [hasOutput, definition?.outputsSchema],
  )
  const treeValue = hasOutput ? run.output : stub
  const hasAnyValue = hasOutput || (stub !== null && Object.keys(stub).length > 0)

  return (
    <div className="flex flex-col">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className={cn(
          'flex w-full items-center gap-2 rounded-[8px] px-2 py-1.5 text-left text-[12px] transition-colors',
          open
            ? 'bg-[var(--surface-2)] text-[var(--text)]'
            : 'text-[var(--text-mute)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
        )}
      >
        {definition && (
          <div
            className="flex size-[20px] shrink-0 items-center justify-center rounded-[5px]"
            style={{ background: definition.color ?? 'var(--surface-3)' }}
          >
            {React.cloneElement(
              getIcon(definition.icon) as React.ReactElement<{ className?: string }>,
              { className: 'size-[12px] text-white' },
            )}
          </div>
        )}
        <span className="min-w-0 flex-1 truncate font-medium text-[var(--text)]" title={label}>
          {label}
        </span>
        <span className="shrink-0 font-mono text-[10.5px] text-[var(--text-faint)]">
          {distance === 1 ? 'direct' : `${distance} hops`}
        </span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 shrink-0 text-[var(--text-faint)] transition-transform duration-150',
            open && 'rotate-180',
          )}
        />
      </button>
      {open && (
        <div className="ml-[26px] mt-1 mb-1.5">
          {hasAnyValue ? (
            <JsonTreeView value={treeValue} nodeId={node.id} initialDepth={0} />
          ) : (
            <p className="text-[11px] italic text-[var(--text-faint)]">
              No output schema declared and no run data yet.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
