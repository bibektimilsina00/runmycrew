import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import type { Node, Edge } from 'reactflow'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'
import { getIcon } from '../../../utils/icon-map'
import { JsonTreeView, type Reference } from '../../right-panel/panels/logs/JsonTreeView'
import type { NodeDefinition } from '../../../types/editorTypes'

interface UpstreamConnectionsSectionProps {
  nodeId: string
}

interface Ancestor {
  node: Node
  definition: NodeDefinition | null
  label: string
  distance: number
  /** Drag-payload reference style for rows in this ancestor's tree.
   *  `$step` when this is the selected node's unique direct parent,
   *  `$node('Label')` otherwise. */
  reference: Reference
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
import { useEditorLayoutStore } from '../../../stores/editorLayoutStore'

export function UpstreamConnectionsSection({ nodeId }: UpstreamConnectionsSectionProps) {
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const edges = useWorkflowEditorStore(s => s.edges)
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)

  // Own collapse + height — independent of the bottom Logs panel so users
  // can keep the inputs preview visible while collapsing the logs (and
  // vice versa). Persisted via the editor layout store.
  const isOpen = useEditorLayoutStore(s => s.inspectorInputsOpen)
  const sectionHeight = useEditorLayoutStore(s => s.inspectorInputsHeight)
  const toggleOpen = useEditorLayoutStore(s => s.toggleInspectorInputs)
  const setSectionHeight = useEditorLayoutStore(s => s.setInspectorInputsHeight)

  const COLLAPSED_HEIGHT = 36
  const totalHeight = isOpen ? sectionHeight : COLLAPSED_HEIGHT

  // ── Resize handle (drag the top edge to grow/shrink) ─────────────────
  const dragState = useRef<{ startY: number; startH: number } | null>(null)
  const [isResizing, setIsResizing] = useState(false)

  const onResizeMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      dragState.current = { startY: e.clientY, startH: sectionHeight }
      setIsResizing(true)
    },
    [sectionHeight],
  )
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const s = dragState.current
      if (!s) return
      // Dragging up grows the section; matches the bottom panel's idiom.
      setSectionHeight(s.startH - (e.clientY - s.startY))
    }
    const onUp = () => {
      dragState.current = null
      setIsResizing(false)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [setSectionHeight])

  const ancestors = useMemo<Ancestor[]>(() => {
    const distance = collectAncestors(nodeId, edges)
    const draft: Array<{ node: Node; definition: NodeDefinition | null; label: string; distance: number }> = []
    for (const [id, d] of distance) {
      const node = nodes.find(n => n.id === id)
      if (!node) continue
      const definition = nodeDefinitions.find(def => def.type === node.type) ?? null
      const label = (node.data?.label as string | undefined) || definition?.name || id
      draft.push({ node, definition, label, distance: d })
    }
    draft.sort((a, b) => a.distance - b.distance)

    // `$step` is valid only when the selected node has exactly one direct
    // parent — otherwise "the step" is ambiguous and we fall back to a label
    // reference for every row.
    const directParents = draft.filter(a => a.distance === 1).length
    return draft.map<Ancestor>(a => ({
      ...a,
      reference:
        a.distance === 1 && directParents === 1
          ? { kind: 'step' }
          : { kind: 'label', label: a.label },
    }))
  }, [nodeId, nodes, edges, nodeDefinitions])

  return (
    <div
      className={cn(
        'shrink-0 border-t border-[var(--border-faint)] flex flex-col overflow-hidden',
        !isResizing && 'transition-[height] duration-300 ease-in-out',
      )}
      style={{ height: totalHeight }}
    >
      {/* Resize handle — only when the section is open. Dragging up grows
          the section like the bottom panel. */}
      {isOpen && (
        <div
          onMouseDown={onResizeMouseDown}
          className="h-1 shrink-0 cursor-row-resize bg-transparent hover:bg-[var(--accent)]/40"
          title="Drag to resize"
        />
      )}

      {/* Header bar — full row clickable. Label sits flush left; the
          chevron toggle is pushed to the right. Count was removed at
          design's request — the ancestor list itself shows the rows. */}
      <button
        type="button"
        onClick={toggleOpen}
        className="flex h-[36px] shrink-0 items-center justify-between px-4 text-left transition-colors hover:bg-[var(--surface)]"
      >
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--text-mute)]">
          Inputs
        </span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 text-[var(--text-faint)] transition-transform duration-150',
            !isOpen && '-rotate-90',
          )}
        />
      </button>

      {/* Body — only mounted when open so collapsed state is genuinely
          zero-cost. */}
      {isOpen && (
        <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-3">
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
      )}
    </div>
  )
}

function AncestorRow({ ancestor }: { ancestor: Ancestor }) {
  const [open, setOpen] = useState(false)
  const { node, definition, distance, label, reference } = ancestor
  const run = useWorkflowEditorStore(s => s.nodeRuns[node.id])

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
            <JsonTreeView value={treeValue} reference={reference} initialDepth={0} />
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
