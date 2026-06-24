import { create } from 'zustand'
import type { Node, Edge } from 'reactflow'
import { useWorkflowEditorStore } from './workflowEditorStore'
import { editorAPI } from '../services/editorAPI'

interface ProposedGraph {
  nodes: Node[]
  edges: Edge[]
}

interface DiffSummary {
  added: string[]
  edited: string[]
  deleted: string[]
}

/**
 * Atomic graph op streamed from the copilot engine. Each tool call from the
 * model lands here as one event so the canvas can paint progressively.
 */
export type StreamingOp =
  | { op: 'add_node'; node_id: string; node: Node }
  | { op: 'update_node'; node_id: string; node: Node }
  | { op: 'remove_node'; node_id: string }
  | { op: 'add_edge'; edge: Edge }
  | { op: 'remove_edge'; source_id: string; target_id: string }
  | { op: 'set_workflow_name'; name: string }

interface CopilotDiffState {
  active: boolean
  /** True while the engine is still streaming ops; false once workflow_proposed (or done) lands. */
  streaming: boolean
  proposed: ProposedGraph | null
  baseline: ProposedGraph | null
  summary: DiffSummary | null
  proposedName: string | null
  /** Open an empty diff overlay (clones current editor graph as baseline). Called on first graph_op of a turn. */
  startStreaming: () => void
  /** Mutate the in-progress proposed graph with one op + recompute summary. */
  applyOp: (op: StreamingOp) => void
  /** Final canonical proposal from workflow_proposed — resolves any drift. */
  setProposal: (graph: ProposedGraph, name?: string | null) => void
  accept: () => Promise<void>
  reject: () => void
}

function diffNodes(baseNodes: Node[], proposedNodes: Node[]): DiffSummary {
  const baseById = new Map(baseNodes.map((n) => [n.id, n]))
  const propIds = new Set(proposedNodes.map((n) => n.id))
  const added: string[] = []
  const edited: string[] = []
  const deleted: string[] = []
  for (const n of proposedNodes) {
    const base = baseById.get(n.id)
    if (!base) added.push(n.id)
    else if (JSON.stringify(base.data) !== JSON.stringify(n.data)) edited.push(n.id)
  }
  for (const n of baseNodes) if (!propIds.has(n.id)) deleted.push(n.id)
  return { added, edited, deleted }
}

function ensureEdgeId(edge: Edge): Edge {
  if (edge.id) return edge
  const sh = edge.sourceHandle ? `-${edge.sourceHandle}` : ''
  return { ...edge, id: `${edge.source}${sh}-${edge.target}` }
}

// Holds a copilot-proposed graph as a pending diff. Streams in op-by-op via
// `applyOp` while the model emits, then `setProposal` lands as the final
// source-of-truth resolve. Accept applies to the editor store; reject discards.
export const useCopilotDiffStore = create<CopilotDiffState>((set, get) => ({
  active: false,
  streaming: false,
  proposed: null,
  baseline: null,
  summary: null,
  proposedName: null,

  startStreaming: () => {
    // Already streaming → no-op (subsequent graph_ops mutate the same proposed).
    if (get().streaming) return
    const editor = useWorkflowEditorStore.getState()
    const baseline: ProposedGraph = {
      nodes: editor.nodes,
      edges: editor.edges,
    }
    // Start the proposed graph as a clone of baseline; ops mutate from here.
    const proposed: ProposedGraph = {
      nodes: [...editor.nodes],
      edges: [...editor.edges],
    }
    set({
      active: true,
      streaming: true,
      baseline,
      proposed,
      summary: { added: [], edited: [], deleted: [] },
      proposedName: null,
    })
  },

  applyOp: (op) => {
    const state = get()
    if (!state.proposed || !state.baseline) {
      // Engine sent graph_op before we initialised. Auto-start so we don't drop it.
      get().startStreaming()
    }
    const current = get().proposed!
    const baseline = get().baseline!

    let nextNodes = current.nodes
    let nextEdges = current.edges

    switch (op.op) {
      case 'add_node': {
        // Replace if already present (engine may re-emit on iteration); else append.
        const existing = nextNodes.findIndex((n) => n.id === op.node.id)
        if (existing >= 0) {
          nextNodes = nextNodes.map((n, i) => (i === existing ? op.node : n))
        } else {
          nextNodes = [...nextNodes, op.node]
        }
        break
      }
      case 'update_node': {
        nextNodes = nextNodes.map((n) => (n.id === op.node_id ? op.node : n))
        break
      }
      case 'remove_node': {
        nextNodes = nextNodes.filter((n) => n.id !== op.node_id)
        nextEdges = nextEdges.filter(
          (e) => e.source !== op.node_id && e.target !== op.node_id,
        )
        break
      }
      case 'add_edge': {
        const edge = ensureEdgeId({ ...op.edge, type: op.edge.type || 'custom' })
        if (!nextEdges.some((e) => e.id === edge.id)) {
          nextEdges = [...nextEdges, edge]
        }
        break
      }
      case 'remove_edge': {
        nextEdges = nextEdges.filter(
          (e) => !(e.source === op.source_id && e.target === op.target_id),
        )
        break
      }
      case 'set_workflow_name': {
        const trimmed = op.name.trim()
        const editor = useWorkflowEditorStore.getState()
        const nameChange = trimmed && trimmed !== editor.workflow?.name
        set({ proposedName: nameChange ? trimmed : null })
        return
      }
    }

    const proposed: ProposedGraph = { nodes: nextNodes, edges: nextEdges }
    set({ proposed, summary: diffNodes(baseline.nodes, nextNodes) })
  },

  setProposal: (graph, name) => {
    const editor = useWorkflowEditorStore.getState()
    const summary = diffNodes(editor.nodes, graph.nodes || [])
    const trimmedName = typeof name === 'string' ? name.trim() : ''
    const currentName = get().proposedName
    const finalName = trimmedName || currentName
    const nameChange = finalName && finalName !== editor.workflow?.name
    if (
      !summary.added.length &&
      !summary.edited.length &&
      !summary.deleted.length &&
      !nameChange
    ) {
      set({
        active: false,
        streaming: false,
        proposed: null,
        baseline: null,
        summary: null,
        proposedName: null,
      })
      return
    }
    set({
      active: true,
      streaming: false,
      proposed: graph,
      baseline: get().baseline ?? { nodes: editor.nodes, edges: editor.edges },
      summary,
      proposedName: nameChange ? finalName : null,
    })
  },

  accept: async () => {
    const { proposed, proposedName } = get()
    if (!proposed) return
    const editor = useWorkflowEditorStore.getState()
    editor.pushHistory()
    editor.setNodes(proposed.nodes || [])
    editor.setEdges(
      (proposed.edges || []).map((e) => ({ ...e, type: e.type || 'custom' })),
    )
    set({
      active: false,
      streaming: false,
      proposed: null,
      baseline: null,
      summary: null,
      proposedName: null,
    })
    if (proposedName && editor.workflow?.id) {
      try {
        const updated = await editorAPI.rename(editor.workflow.id, proposedName)
        useWorkflowEditorStore.getState().setWorkflow(updated)
      } catch {
        // Rename failure leaves graph accepted; topbar still shows old name.
      }
    }
  },

  reject: () =>
    set({
      active: false,
      streaming: false,
      proposed: null,
      baseline: null,
      summary: null,
      proposedName: null,
    }),
}))
