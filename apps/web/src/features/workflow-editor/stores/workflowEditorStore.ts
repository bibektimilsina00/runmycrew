import { create } from 'zustand'
import { applyNodeChanges, applyEdgeChanges, type Node, type Edge, type OnNodesChange, type OnEdgesChange } from 'reactflow'
import type { NodeDefinition } from '../types/editorTypes'
import type { SaveState, WorkflowDetail } from '../types/editorTypes'

interface GraphSnapshot {
  nodes: Node[]
  edges: Edge[]
}

const HISTORY_LIMIT = 50
const PASTE_OFFSET = 40

interface WorkflowEditorState {
  // Loaded workflow meta
  workflow: WorkflowDetail | null
  setWorkflow: (w: WorkflowDetail) => void

  // Node definitions loaded from API
  nodeDefinitions: NodeDefinition[]
  setNodeDefinitions: (defs: NodeDefinition[]) => void

  // ReactFlow graph state — the store is the single source of truth.
  nodes: Node[]
  edges: Edge[]
  setNodes: (nodes: Node[] | ((nodes: Node[]) => Node[])) => void
  setEdges: (edges: Edge[] | ((edges: Edge[]) => Edge[])) => void
  onNodesChange: OnNodesChange
  onEdgesChange: OnEdgesChange

  // Node mutations
  removeNode: (id: string) => void
  toggleNodeLock: (id: string) => void
  duplicateNode: (id: string) => void
  toggleNodeHandleDirection: (id: string) => void

  // Undo / redo
  past: GraphSnapshot[]
  future: GraphSnapshot[]
  pushHistory: () => void
  undo: () => void
  redo: () => void

  // Clipboard + selection
  clipboard: GraphSnapshot | null
  copySelection: () => void
  paste: () => void
  selectAll: () => void
  deselectAll: () => void
  deleteSelected: () => void

  // Save state
  saveState: SaveState
  setSaveState: (s: SaveState) => void
  versionVector: number
  setVersionVector: (v: number) => void

  // UI state
  selectedNodeId: string | null
  setSelectedNodeId: (id: string | null) => void
  inspectorOpen: boolean
  setInspectorOpen: (open: boolean) => void
  inspectorTab: 'config' | 'copilot' | 'library' | 'logs' | 'test'
  setInspectorTab: (tab: WorkflowEditorState['inspectorTab']) => void

  // Reset when leaving editor
  reset: () => void
}

export const useWorkflowEditorStore = create<WorkflowEditorState>((set, get) => ({
  workflow: null,
  setWorkflow: (workflow) => set({ workflow }),

  nodeDefinitions: [],
  setNodeDefinitions: (nodeDefinitions) => set({ nodeDefinitions }),

  nodes: [],
  edges: [],
  setNodes: (nodes) => set(s => ({ nodes: typeof nodes === 'function' ? nodes(s.nodes) : nodes })),
  setEdges: (edges) => set(s => ({ edges: typeof edges === 'function' ? edges(s.edges) : edges })),
  onNodesChange: (changes) => set(s => ({ nodes: applyNodeChanges(changes, s.nodes) })),
  onEdgesChange: (changes) => set(s => ({ edges: applyEdgeChanges(changes, s.edges) })),

  removeNode: (id) => {
    get().pushHistory()
    set(s => ({
      nodes: s.nodes.filter(n => n.id !== id),
      edges: s.edges.filter(e => e.source !== id && e.target !== id),
      saveState: 'unsaved' as SaveState,
    }))
  },

  toggleNodeLock: (id) => set(s => ({
    nodes: s.nodes.map(n =>
      n.id === id ? { ...n, data: { ...n.data, locked: !n.data?.locked } } : n,
    ),
    saveState: 'unsaved' as SaveState,
  })),

  duplicateNode: (id) => {
    const node = get().nodes.find(n => n.id === id)
    if (!node) return
    get().pushHistory()
    const newNode: Node = {
      ...node,
      id: crypto.randomUUID(),
      position: { x: node.position.x + 30, y: node.position.y + 30 },
      selected: false,
    }
    set(s => ({
      nodes: [...s.nodes, newNode],
      saveState: 'unsaved' as SaveState,
    }))
  },

  toggleNodeHandleDirection: (id) => set(s => ({
    nodes: s.nodes.map(n =>
      n.id === id
        ? { ...n, data: { ...n.data, handleDirection: n.data?.handleDirection === 'vertical' ? 'horizontal' : 'vertical' } }
        : n,
    ),
    saveState: 'unsaved' as SaveState,
  })),

  // ── Undo / redo ───────────────────────────────────────────────────────────
  past: [],
  future: [],
  pushHistory: () => set(s => ({
    past: [...s.past, { nodes: s.nodes, edges: s.edges }].slice(-HISTORY_LIMIT),
    future: [],
  })),
  undo: () => set(s => {
    const prev = s.past[s.past.length - 1]
    if (!prev) return {}
    return {
      past: s.past.slice(0, -1),
      future: [{ nodes: s.nodes, edges: s.edges }, ...s.future],
      nodes: prev.nodes,
      edges: prev.edges,
      saveState: 'unsaved' as SaveState,
    }
  }),
  redo: () => set(s => {
    const next = s.future[0]
    if (!next) return {}
    return {
      past: [...s.past, { nodes: s.nodes, edges: s.edges }],
      future: s.future.slice(1),
      nodes: next.nodes,
      edges: next.edges,
      saveState: 'unsaved' as SaveState,
    }
  }),

  // ── Clipboard + selection ─────────────────────────────────────────────────
  clipboard: null,
  copySelection: () => {
    const { nodes, edges } = get()
    const selected = nodes.filter(n => n.selected)
    if (!selected.length) return
    const ids = new Set(selected.map(n => n.id))
    const innerEdges = edges.filter(e => ids.has(e.source) && ids.has(e.target))
    set({ clipboard: { nodes: selected, edges: innerEdges } })
  },
  paste: () => {
    const clip = get().clipboard
    if (!clip || !clip.nodes.length) return
    get().pushHistory()
    const idMap = new Map<string, string>()
    const newNodes = clip.nodes.map(n => {
      const id = crypto.randomUUID()
      idMap.set(n.id, id)
      return {
        ...n,
        id,
        position: { x: n.position.x + PASTE_OFFSET, y: n.position.y + PASTE_OFFSET },
        selected: true,
      }
    })
    const newEdges = clip.edges.map(e => ({
      ...e,
      id: crypto.randomUUID(),
      source: idMap.get(e.source) ?? e.source,
      target: idMap.get(e.target) ?? e.target,
      selected: false,
    }))
    set(s => ({
      nodes: [...s.nodes.map(n => (n.selected ? { ...n, selected: false } : n)), ...newNodes],
      edges: [...s.edges, ...newEdges],
      saveState: 'unsaved' as SaveState,
    }))
  },
  selectAll: () => set(s => ({ nodes: s.nodes.map(n => (n.selected ? n : { ...n, selected: true })) })),
  deselectAll: () => set(s => ({ nodes: s.nodes.map(n => (n.selected ? { ...n, selected: false } : n)) })),
  deleteSelected: () => {
    const ids = new Set(get().nodes.filter(n => n.selected).map(n => n.id))
    const selectedEdges = get().edges.filter(e => e.selected).map(e => e.id)
    if (!ids.size && !selectedEdges.length) return
    get().pushHistory()
    const edgeIds = new Set(selectedEdges)
    set(s => ({
      nodes: s.nodes.filter(n => !ids.has(n.id)),
      edges: s.edges.filter(e => !edgeIds.has(e.id) && !ids.has(e.source) && !ids.has(e.target)),
      saveState: 'unsaved' as SaveState,
    }))
  },

  saveState: 'saved',
  setSaveState: (saveState) => set({ saveState }),
  versionVector: 0,
  setVersionVector: (versionVector) => set({ versionVector }),

  selectedNodeId: null,
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
  inspectorOpen: false,
  setInspectorOpen: (inspectorOpen) => set({ inspectorOpen }),
  inspectorTab: 'config',
  setInspectorTab: (inspectorTab) => set({ inspectorTab }),

  reset: () => set({
    workflow: null,
    nodes: [],
    edges: [],
    nodeDefinitions: [],
    past: [],
    future: [],
    clipboard: null,
    saveState: 'saved',
    versionVector: 0,
    selectedNodeId: null,
    inspectorOpen: false,
    inspectorTab: 'config',
  }),
}))
