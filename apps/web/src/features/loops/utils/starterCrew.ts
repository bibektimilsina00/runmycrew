import { CREW_PRESETS } from './crewPresets'

// A serialized graph matching the shape the workflow editor persists
// (see `cleanGraph` in features/workflow-editor). Kept intentionally minimal —
// only durable fields — so the seeded loop hydrates identically to a
// hand-drawn one.
export interface StarterGraph {
  nodes: Array<{ id: string; type: string; position: { x: number; y: number }; data: { label: string; properties: Record<string, unknown> } }>
  edges: Array<{ id: string; source: string; target: string }>
}

// Crews are conversational by default — the natural entry is the hosted chat.
const TRIGGER_TYPE = 'trigger.chat_app'

// Ordered spec for the starter crew: the chat trigger, then the orchestrator
// and the three worker roles left→right. Each role points at a CrewPreset id so
// labels + default properties stay in one place.
const CHAIN: Array<{ presetId: string; label: string }> = [
  { presetId: 'crew', label: 'Crew' },
  { presetId: 'planner', label: 'Planner' },
  { presetId: 'worker', label: 'Worker' },
  { presetId: 'reviewer', label: 'Reviewer' },
]

const COL_GAP = 320
const ROW_Y = 200

/**
 * Build the starter crew graph for a brand-new loop, given the set of node
 * `type` strings that actually exist in the backend. Any role whose underlying
 * node type is missing is skipped (along with the edges touching it), so the
 * seed never produces a broken node. Returns an empty graph if nothing resolves.
 */
export function buildStarterCrew(availableTypes: Set<string>): StarterGraph {
  const nodes: StarterGraph['nodes'] = []
  const edges: StarterGraph['edges'] = []

  // Track the id assigned to each role (or the trigger) so edges can reference
  // only nodes that were actually created.
  const idByKey = new Map<string, string>()

  // Trigger (leftmost) — only seed it if the manual trigger exists.
  if (availableTypes.has(TRIGGER_TYPE)) {
    const id = crypto.randomUUID()
    idByKey.set('trigger', id)
    nodes.push({
      id,
      type: TRIGGER_TYPE,
      position: { x: 0, y: ROW_Y },
      data: { label: 'Chat App', properties: {} },
    })
  }

  CHAIN.forEach(({ presetId, label }, i) => {
    const preset = CREW_PRESETS.find(p => p.id === presetId)
    if (!preset || !availableTypes.has(preset.nodeType)) return
    const id = crypto.randomUUID()
    idByKey.set(presetId, id)
    nodes.push({
      id,
      type: preset.nodeType,
      // +1 so the trigger occupies the first column even when present.
      position: { x: (i + 1) * COL_GAP, y: ROW_Y },
      data: { label, properties: { ...preset.defaultProperties } },
    })
  })

  const link = (fromKey: string, toKey: string) => {
    const source = idByKey.get(fromKey)
    const target = idByKey.get(toKey)
    if (!source || !target) return
    edges.push({ id: crypto.randomUUID(), source, target })
  }

  // trigger→Crew, Crew→Planner, Planner→Worker, Worker→Reviewer,
  // and the loop-back Reviewer→Planner.
  link('trigger', 'crew')
  link('crew', 'planner')
  link('planner', 'worker')
  link('worker', 'reviewer')
  link('reviewer', 'planner')

  return { nodes, edges }
}
