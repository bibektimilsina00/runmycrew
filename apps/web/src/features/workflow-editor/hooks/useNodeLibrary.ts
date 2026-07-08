import { useMemo, useState } from 'react'
import { useReactFlow } from 'reactflow'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import type { NodeDefinition } from '../types/editorTypes'
import { CREW_PRESETS, type CrewPreset } from '@/features/loops/utils/crewPresets'

const CATEGORY_ORDER = ['trigger', 'action', 'ai', 'logic', 'browser', 'integration'] as const

// Loop Engineering shows a focused palette of AI-orchestration nodes only —
// the 100s of integration/action/browser nodes are hidden so the canvas reads
// as "autonomous agents in verified loops".
const LOOP_CATEGORIES = new Set(['trigger', 'ai', 'logic'])

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
  const mode = useWorkflowEditorStore(s => s.mode)
  const setNodes = useWorkflowEditorStore(s => s.setNodes)
  const pushHistory = useWorkflowEditorStore(s => s.pushHistory)
  const [query, setQuery] = useState('')
  const { screenToFlowPosition } = useReactFlow()

  // In a crew, restrict the palette to AI-orchestration categories BEFORE
  // search + grouping so both respect the focused set. Driven by the store's
  // `mode` (set from the /crews/:id route); workflows keep the full palette.
  const loopMode = mode === 'crew'
  const available = useMemo(
    () => (loopMode ? nodeDefinitions.filter(d => LOOP_CATEGORIES.has(d.category)) : nodeDefinitions),
    [nodeDefinitions, loopMode],
  )

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim()
    if (!q) return available
    return available.filter(
      d => d.name.toLowerCase().includes(q) || d.description.toLowerCase().includes(q),
    )
  }, [available, query])

  // Nodes are grouped by `category` (Triggers/Actions/AI/…). Inside the
  // Integrations bucket, we further split by `brand` so all google nodes
  // (gmail, gdrive, gsheets, …) collapse under a "Google" subgroup and
  // stop drowning the list. Nodes without a brand stay ungrouped at the
  // top of the bucket. Same structure as before, just with an optional
  // per-brand sub-map inside each category entry.
  const grouped = useMemo(() => {
    const byCat = new Map<string, typeof filtered>()
    for (const def of filtered) {
      const list = byCat.get(def.category) ?? []
      list.push(def)
      byCat.set(def.category, list)
    }
    return CATEGORY_ORDER
      .filter(c => byCat.has(c))
      .map(c => {
        const defs = byCat.get(c)!
        const byBrand = new Map<string, typeof defs>()
        const unbranded: typeof defs = []
        for (const d of defs) {
          if (d.brand) {
            const list = byBrand.get(d.brand) ?? []
            list.push(d)
            byBrand.set(d.brand, list)
          } else {
            unbranded.push(d)
          }
        }
        // Preserve unbranded first, then brands alphabetically — one bucket
        // per brand, each sorted by node name for a stable read.
        const brands = Array.from(byBrand.keys()).sort()
        return {
          category: c,
          defs,
          unbranded,
          brands: brands.map(b => ({ brand: b, defs: byBrand.get(b)!.slice().sort((a, z) => a.name.localeCompare(z.name)) })),
        }
      })
  }, [filtered])

  // In loop mode the palette shows curated role-agent presets ("Crew") instead
  // of the raw category nodes. A preset is only surfaced when its underlying
  // nodeType actually exists in the loaded definitions, so a missing backend
  // node simply drops from the list rather than spawning a broken node.
  const presets = useMemo<CrewPreset[]>(() => {
    if (!loopMode) return []
    const types = new Set(nodeDefinitions.map(d => d.type))
    const q = query.toLowerCase().trim()
    return CREW_PRESETS.filter(p => types.has(p.nodeType)).filter(p => {
      if (!q) return true
      return p.label.toLowerCase().includes(q) || p.description.toLowerCase().includes(q)
    })
  }, [loopMode, nodeDefinitions, query])

  const positionForSpawn = () => {
    const canvasCenterX = (window.innerWidth - 360) / 2
    const canvasCenterY = window.innerHeight / 2
    const position = screenToFlowPosition({ x: canvasCenterX, y: canvasCenterY })
    position.x += (Math.random() - 0.5) * 80
    position.y += (Math.random() - 0.5) * 80
    return position
  }

  const spawnNode = (def: NodeDefinition) => {
    const position = positionForSpawn()
    pushHistory()
    setNodes(ns => [...ns, {
      id: crypto.randomUUID(),
      type: def.type,
      position,
      data: { label: def.name, properties: {} },
    }])
  }

  const spawnPreset = (preset: CrewPreset) => {
    const position = positionForSpawn()
    pushHistory()
    setNodes(ns => [...ns, {
      id: crypto.randomUUID(),
      type: preset.nodeType,
      position,
      data: { label: preset.label, properties: { ...preset.defaultProperties } },
    }])
  }

  const onDragStart = (e: React.DragEvent, def: NodeDefinition) => {
    e.dataTransfer.setData('application/reactflow', def.type)
    e.dataTransfer.effectAllowed = 'move'
  }

  const onDragStartPreset = (e: React.DragEvent, preset: CrewPreset) => {
    e.dataTransfer.setData('application/reactflow', preset.nodeType)
    e.dataTransfer.effectAllowed = 'move'
  }

  return { query, setQuery, grouped, spawnNode, onDragStart, loopMode, presets, spawnPreset, onDragStartPreset }
}
