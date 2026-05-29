import { useMemo, useState } from 'react'
import { useReactFlow } from 'reactflow'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import type { NodeDefinition } from '../types/editorTypes'

const CATEGORY_ORDER = ['trigger', 'action', 'ai', 'logic', 'browser', 'integration'] as const

export const CATEGORY_LABEL: Record<string, string> = {
  trigger:     'Triggers',
  action:      'Actions',
  ai:          'AI',
  logic:       'Logic',
  browser:     'Browser',
  integration: 'Integrations',
}

export function useNodeLibrary() {
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)
  const setNodes = useWorkflowEditorStore(s => s.setNodes)
  const pushHistory = useWorkflowEditorStore(s => s.pushHistory)
  const [query, setQuery] = useState('')
  const { screenToFlowPosition } = useReactFlow()

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim()
    if (!q) return nodeDefinitions
    return nodeDefinitions.filter(
      d => d.name.toLowerCase().includes(q) || d.description.toLowerCase().includes(q),
    )
  }, [nodeDefinitions, query])

  const grouped = useMemo(() => {
    const map = new Map<string, typeof filtered>()
    for (const def of filtered) {
      const list = map.get(def.category) ?? []
      list.push(def)
      map.set(def.category, list)
    }
    return CATEGORY_ORDER
      .filter(c => map.has(c))
      .map(c => ({ category: c, defs: map.get(c)! }))
  }, [filtered])

  const spawnNode = (def: NodeDefinition) => {
    const canvasCenterX = (window.innerWidth - 360) / 2
    const canvasCenterY = window.innerHeight / 2
    const position = screenToFlowPosition({ x: canvasCenterX, y: canvasCenterY })
    position.x += (Math.random() - 0.5) * 80
    position.y += (Math.random() - 0.5) * 80
    pushHistory()
    setNodes(ns => [...ns, {
      id: crypto.randomUUID(),
      type: def.type,
      position,
      data: { label: def.name, properties: {} },
    }])
  }

  const onDragStart = (e: React.DragEvent, def: NodeDefinition) => {
    e.dataTransfer.setData('application/reactflow', def.type)
    e.dataTransfer.effectAllowed = 'move'
  }

  return { query, setQuery, grouped, spawnNode, onDragStart }
}
