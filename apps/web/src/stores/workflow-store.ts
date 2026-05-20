import { create } from 'zustand'
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
} from 'reactflow'
import type {
  Connection,
  Edge,
  EdgeChange,
  Node,
  NodeChange,
  OnConnect,
  OnEdgesChange,
  OnNodesChange,
} from 'reactflow'

import type { NodeDefinition } from '@fuse/node-definitions'

interface WorkflowState {
  nodes: Node[]
  edges: Edge[]
  nodeDefinitions: NodeDefinition[]
  onNodesChange: OnNodesChange
  onEdgesChange: OnEdgesChange
  onConnect: OnConnect
  setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void
  setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void
  setNodeDefinitions: (definitions: NodeDefinition[]) => void
  addNode: (node: Node) => void
  updateNodeData: (id: string, data: any) => void
  removeNode: (id: string) => void
  toggleNodeLock: (id: string) => void
  duplicateNode: (id: string) => void
  toggleNodeHandleDirection: (id: string) => void
  selectedNodeId: string | null
  setSelectedNodeId: (id: string | null) => void
  nodeSelectionTimestamp: number
  loadWorkflow: (workflow: any) => void
  // Workflow metadata
  workflowId: string | null
  workflowName: string | null
  workflowVersion: number
  isDirty: boolean
  isActive: boolean
  setIsActive: (active: boolean) => void
  markDirty: () => void
  markSaved: (version: number) => void
  applyRemoteGraphPatch: (patch: GraphPatch) => void
  // Canvas lock — prevents editing (dragging, connecting, selecting)
  workflowLocked: boolean
  setWorkflowLocked: (locked: boolean) => void
  // Undo / redo
  undoStack: Array<{ nodes: Node[]; edges: Edge[] }>
  redoStack: Array<{ nodes: Node[]; edges: Edge[] }>
  snapshot: () => void
  undo: () => void
  redo: () => void
  canUndo: () => boolean
  canRedo: () => boolean
}

export type GraphPatch =
  | { operation: 'node.position'; nodeId: string; position: { x: number; y: number } }
  | { operation: 'graph.replace'; nodes: Node[]; edges: Edge[]; version?: number }

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  nodeDefinitions: [],
  workflowId: null,
  workflowName: null,
  workflowVersion: 0,
  isDirty: false,
  isActive: true,
  setIsActive: (active) => set({ isActive: active }),
  markDirty: () => set({ isDirty: true }),
  markSaved: (workflowVersion) => set({ workflowVersion, isDirty: false }),
  applyRemoteGraphPatch: (patch) => {
    if (patch.operation === 'node.position') {
      set(state => ({
        nodes: state.nodes.map(node => (
          node.id === patch.nodeId ? { ...node, position: patch.position } : node
        )),
      }))
      return
    }
    set({
      nodes: patch.nodes,
      edges: patch.edges,
      workflowVersion: patch.version ?? get().workflowVersion,
      isDirty: false,
    })
  },
  workflowLocked: false,
  setWorkflowLocked: (locked) => set({ workflowLocked: locked }),
  undoStack: [],
  redoStack: [],
  snapshot: () => {
    const { nodes, edges, undoStack } = get()
    const MAX = 50
    set({
      undoStack: [...undoStack.slice(-MAX + 1), { nodes: [...nodes], edges: [...edges] }],
      redoStack: [],  // snapshot clears redo
    })
  },
  undo: () => {
    const { nodes, edges, undoStack, redoStack } = get()
    if (undoStack.length === 0) return
    const prev = undoStack[undoStack.length - 1]
    set({
      nodes: prev.nodes,
      edges: prev.edges,
      undoStack: undoStack.slice(0, -1),
      redoStack: [...redoStack, { nodes: [...nodes], edges: [...edges] }],
    })
  },
  redo: () => {
    const { nodes, edges, undoStack, redoStack } = get()
    if (redoStack.length === 0) return
    const next = redoStack[redoStack.length - 1]
    set({
      nodes: next.nodes,
      edges: next.edges,
      undoStack: [...undoStack, { nodes: [...nodes], edges: [...edges] }],
      redoStack: redoStack.slice(0, -1),
    })
  },
  canUndo: () => get().undoStack.length > 0,
  canRedo: () => get().redoStack.length > 0,
  onNodesChange: (changes: NodeChange[]) => {
    set({ nodes: applyNodeChanges(changes, get().nodes), isDirty: true })
  },
  onEdgesChange: (changes: EdgeChange[]) => {
    set({ edges: applyEdgeChanges(changes, get().edges), isDirty: true })
  },
  onConnect: (connection: Connection) => {
    set({ edges: addEdge(connection, get().edges), isDirty: true })
  },
  setNodes: (nodes) => set(state => ({ nodes: typeof nodes === 'function' ? nodes(state.nodes) : nodes, isDirty: true })),
  setEdges: (edges) => set(state => ({ edges: typeof edges === 'function' ? edges(state.edges) : edges, isDirty: true })),
  setNodeDefinitions: (nodeDefinitions: NodeDefinition[]) => set({ nodeDefinitions }),
  addNode: (node: Node) => set({ nodes: [...get().nodes, node] }),
  updateNodeData: (id: string, data: any) => {
    set({
      nodes: get().nodes.map((node) => {
        if (node.id === id) {
          return { ...node, data: { ...node.data, ...data } };
        }
        return node;
      }),
    });
  },
  removeNode: (id: string) => {
    get().snapshot()
    const current = get().nodes
    const removedNode = current.find(n => n.id === id)

    // Convert children's relative positions to absolute before unparenting
    const updatedNodes = current
      .filter(n => n.id !== id)
      .map(n => {
        if (n.parentNode !== id) return n
        const absX = (removedNode?.position.x ?? 0) + n.position.x
        const absY = (removedNode?.position.y ?? 0) + n.position.y
        return { ...n, parentNode: undefined, extent: undefined, position: { x: absX, y: absY }, data: { ...n.data, parentId: undefined } }
      })

    set({
      nodes: updatedNodes,
      edges: get().edges.filter((edge) => edge.source !== id && edge.target !== id),
      selectedNodeId: get().selectedNodeId === id ? null : get().selectedNodeId
    })
  },
  toggleNodeLock: (id: string) => {
    set({
      nodes: get().nodes.map((node) => {
        if (node.id === id) {
          const isLocked = !node.data?.locked
          return {
            ...node,
            draggable: !isLocked,
            selectable: !isLocked,
            deletable: !isLocked,
            data: { ...node.data, locked: isLocked }
          }
        }
        return node
      })
    })
  },
  duplicateNode: (id: string) => {
    const node = get().nodes.find(n => n.id === id)
    if (!node) return
 
    const newNode: Node = {
      ...node,
      id: crypto.randomUUID(),
      position: { x: node.position.x + 20, y: node.position.y + 20 },
      selected: false,
    }
    set({ nodes: [...get().nodes, newNode] })
  },
  toggleNodeHandleDirection: (id: string) => {
    set({
      nodes: get().nodes.map((node) => {
        if (node.id === id) {
          const newDirection = node.data?.handleDirection === 'horizontal' ? 'vertical' : 'horizontal'
          return {
            ...node,
            data: { ...node.data, handleDirection: newDirection }
          }
        }
        return node
      })
    })
  },
  selectedNodeId: null,
  nodeSelectionTimestamp: Date.now(),
  setSelectedNodeId: (id: string | null) => set({ 
    selectedNodeId: id,
    nodeSelectionTimestamp: Date.now()
  }),
  loadWorkflow: (workflow: any) => {
    const rawNodes = workflow.graph?.nodes || []
    const edges = workflow.graph?.edges || []

    // ReactFlow requires parent nodes before children — use centralized sort
    // (inline to avoid circular import from loop-utils)
    const nodeMap = new Map(rawNodes.map((n: any) => [n.id, n]))
    const result: any[] = []
    const added = new Set<string>()
    const addNode = (node: any) => {
      if (added.has(node.id)) return
      if (node.parentNode && !added.has(node.parentNode)) {
        const parent = nodeMap.get(node.parentNode)
        if (parent) addNode(parent)
      }
      result.push(node)
      added.add(node.id)
    }
    rawNodes.forEach(addNode)
    const nodes = result

    set({
      nodes,
      edges,
      selectedNodeId: null,
      nodeSelectionTimestamp: Date.now(),
      workflowId: workflow.id ?? null,
      workflowName: workflow.name ?? null,
      workflowVersion: workflow.version_vector ?? 0,
      isDirty: false,
      isActive: workflow.is_active !== false,
    })
  }
}))
