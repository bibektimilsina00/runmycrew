import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { EdgeProps, Node } from 'reactflow'
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
} from 'reactflow'
import { ChevronDown, Plus, Search, Trash2, X } from 'lucide-react'
import { createPortal } from 'react-dom'

import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'

const CATEGORY_ORDER = ['trigger', 'ai', 'integration', 'logic', 'db', 'action']
const CATEGORY_LABELS: Record<string, string> = {
  trigger: 'Triggers',
  ai: 'AI',
  integration: 'Integrations',
  logic: 'Logic',
  db: 'Databases',
  action: 'Actions',
}

interface NodePickerProps {
  anchorX: number
  anchorY: number
  onSelect: (type: string) => void
  onClose: () => void
}

const NodePicker = ({ anchorX, anchorY, onSelect, onClose }: NodePickerProps) => {
  const [search, setSearch] = useState('')
  const [openCategory, setOpenCategory] = useState<string | null>('ai')
  const ref = useRef<HTMLDivElement>(null)
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)

  useEffect(() => {
    const handleMouseDown = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as globalThis.Node)) onClose()
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('mousedown', handleMouseDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handleMouseDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose])

  const categories = useMemo(() => {
    const map = new Map<string, typeof nodeDefinitions>()
    for (const definition of nodeDefinitions) {
      const category = definition.category || 'action'
      map.set(category, [...(map.get(category) || []), definition])
    }

    const ordered = CATEGORY_ORDER
      .filter(key => map.has(key))
      .map(key => ({
        key,
        label: CATEGORY_LABELS[key] || key,
        nodes: map.get(key) || [],
      }))

    for (const [key, nodes] of map) {
      if (!CATEGORY_ORDER.includes(key)) ordered.push({ key, label: key, nodes })
    }

    return ordered
  }, [nodeDefinitions])

  const query = search.toLowerCase().trim()
  const searchResults = query
    ? nodeDefinitions.filter(definition =>
      definition.name.toLowerCase().includes(query) ||
      definition.category?.toLowerCase().includes(query),
    )
    : []

  const width = 220
  const maxHeight = 360
  const left = anchorX + width > window.innerWidth ? anchorX - width : anchorX
  const top = anchorY + maxHeight > window.innerHeight ? anchorY - maxHeight : anchorY

  return createPortal(
    <div
      ref={ref}
      className="fixed z-[9999] flex flex-col rounded-[11px] border border-[var(--border)] bg-[var(--bg-2)] shadow-[var(--shadow-dropdown)]"
      style={{ left, top, width, maxHeight }}
    >
      <div className="flex-shrink-0 border-b border-[var(--border-faint)] p-2">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-faint)]" />
          <input
            autoFocus
            value={search}
            onChange={event => setSearch(event.target.value)}
            placeholder="Search nodes..."
            className="w-full rounded-[8px] border border-[var(--border-faint)] bg-[var(--bg)] py-1.5 pl-7 pr-7 text-[12px] text-[var(--text)] outline-none transition-colors placeholder:text-[var(--text-faint)] focus:border-[var(--border-soft)]"
          />
          {search && (
            <button
              type="button"
              onClick={() => setSearch('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-mute)] transition-colors hover:text-[var(--text)]"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-1">
        {query ? (
          searchResults.length === 0 ? (
            <p className="px-3 py-4 text-center text-[11px] text-[var(--text-faint)]">No results</p>
          ) : (
            searchResults.map(definition => (
              <NodePickerItem key={definition.type} node={definition} onSelect={onSelect} />
            ))
          )
        ) : (
          categories.map(({ key, label, nodes }) => (
            <div key={key}>
              <button
                type="button"
                onClick={() => setOpenCategory(openCategory === key ? null : key)}
                className="flex w-full items-center justify-between px-3 py-1.5 transition-colors hover:bg-[var(--surface)]"
              >
                <span className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-faint)]">
                  {label} <span className="font-normal normal-case opacity-50">{nodes.length}</span>
                </span>
                <ChevronDown className={cn('h-3 w-3 text-[var(--text-faint)] transition-transform', openCategory !== key && '-rotate-90')} />
              </button>
              {openCategory === key && nodes.map(definition => (
                <NodePickerItem key={definition.type} node={definition} onSelect={onSelect} />
              ))}
            </div>
          ))
        )}
      </div>
    </div>,
    document.body,
  )
}

interface NodePickerItemProps {
  node: { type: string; name: string; icon: string; color?: string }
  onSelect: (type: string) => void
}

const NodePickerItem = ({ node, onSelect }: NodePickerItemProps) => (
  <button
    type="button"
    onClick={() => onSelect(node.type)}
    className="flex w-full items-center gap-2 px-3 py-1.5 text-left transition-colors hover:bg-[var(--surface)]"
  >
    <div
      className="flex size-5 flex-shrink-0 items-center justify-center rounded-md"
      style={{ backgroundColor: node.color || '#3b82f6' }}
    >
      <span className="text-[10px] font-bold text-white">{node.name.slice(0, 1)}</span>
    </div>
    <span className="truncate text-[12px] text-[var(--text)]">{node.name}</span>
  </button>
)

export const CustomEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style,
  markerEnd,
}: EdgeProps) => {
  const [hovered, setHovered] = useState(false)
  const [pickerPos, setPickerPos] = useState<{ x: number; y: number } | null>(null)
  const edges = useWorkflowEditorStore(s => s.edges)
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const setEdges = useWorkflowEditorStore(s => s.setEdges)
  const setNodes = useWorkflowEditorStore(s => s.setNodes)
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)
  const setSaveState = useWorkflowEditorStore(s => s.setSaveState)

  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 12,
  })

  const handleDelete = useCallback(() => {
    setEdges(edges.filter(edge => edge.id !== id))
    setSaveState('unsaved')
  }, [edges, id, setEdges, setSaveState])

  const handleAddClick = useCallback((event: React.MouseEvent) => {
    event.stopPropagation()
    setPickerPos({ x: event.clientX, y: event.clientY })
  }, [])

  const handleNodeSelect = useCallback((nodeType: string) => {
    setPickerPos(null)
    const edge = edges.find(item => item.id === id)
    if (!edge) return

    const definition = nodeDefinitions.find(item => item.type === nodeType)
    const defaultWidth = 168
    const newNode: Node = {
      id: `${nodeType}-${crypto.randomUUID()}`,
      type: nodeType,
      position: {
        x: (sourceX + targetX) / 2 - (defaultWidth / 2),
        y: (sourceY + targetY) / 2 - 40,
      },
      data: { label: definition?.name || '', properties: {} },
    }

    setEdges([
      ...edges.filter(item => item.id !== id),
      {
        id: `${edge.source}-${newNode.id}`,
        source: edge.source,
        target: newNode.id,
        sourceHandle: edge.sourceHandle || 'source',
        targetHandle: 'target',
        type: 'custom',
        style: { stroke: 'var(--border)', strokeWidth: 2 },
      },
      {
        id: `${newNode.id}-${edge.target}`,
        source: newNode.id,
        target: edge.target,
        sourceHandle: 'source',
        targetHandle: edge.targetHandle || 'target',
        type: 'custom',
        style: { stroke: 'var(--border)', strokeWidth: 2 },
      },
    ])
    setNodes([...nodes, newNode])
    setSaveState('unsaved')
  }, [edges, id, nodeDefinitions, nodes, setEdges, setNodes, setSaveState, sourceX, sourceY, targetX, targetY])

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          stroke: hovered ? 'var(--text-dim)' : 'var(--border)',
          strokeWidth: hovered ? 2.5 : 2,
        }}
        interactionWidth={20}
      />
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={20}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{ cursor: 'pointer' }}
      />

      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            pointerEvents: 'all',
          }}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          className="nodrag nopan"
        >
          {hovered && (
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handleAddClick}
                title="Insert node"
                className="flex h-5 w-5 items-center justify-center rounded-[6px] border border-[var(--border-faint)] bg-[var(--surface)] text-[var(--text-mute)] shadow-[var(--shadow-float)] transition-[background,border-color,color,transform] duration-[120ms] hover:border-[var(--border-soft)] hover:bg-[var(--surface-2)] hover:text-[var(--text)] active:scale-[0.97]"
              >
                <Plus className="h-3 w-3" />
              </button>
              <button
                type="button"
                onClick={handleDelete}
                title="Delete edge"
                className="flex h-5 w-5 items-center justify-center rounded-[6px] border border-[var(--border-faint)] bg-[var(--surface)] text-[var(--err)] shadow-[var(--shadow-float)] transition-[background,border-color,color,transform] duration-[120ms] hover:border-[oklch(0.70_0.18_22/0.25)] hover:bg-[oklch(0.70_0.18_22/0.10)] hover:text-[var(--err)] active:scale-[0.97]"
              >
                <Trash2 className="h-2.5 w-2.5" />
              </button>
            </div>
          )}
        </div>
      </EdgeLabelRenderer>

      {pickerPos && (
        <NodePicker
          anchorX={pickerPos.x}
          anchorY={pickerPos.y}
          onSelect={handleNodeSelect}
          onClose={() => setPickerPos(null)}
        />
      )}
    </>
  )
}
