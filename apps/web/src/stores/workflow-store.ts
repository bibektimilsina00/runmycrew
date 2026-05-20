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
  setEdges: (edges: Edge[]) => void
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
  isActive: boolean
  setIsActive: (active: boolean) => void
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  nodeDefinitions: [],
  workflowId: null,
  workflowName: null,
  isActive: true,
  setIsActive: (active) => set({ isActive: active }),
  onNodesChange: (changes: NodeChange[]) => {
    set({ nodes: applyNodeChanges(changes, get().nodes) })
  },
  onEdgesChange: (changes: EdgeChange[]) => {
    set({ edges: applyEdgeChanges(changes, get().edges) })
  },
  onConnect: (connection: Connection) => {
    set({ edges: addEdge(connection, get().edges) })
  },
  setNodes: (nodes) => set(state => ({ nodes: typeof nodes === 'function' ? nodes(state.nodes) : nodes })),
  setEdges: (edges: Edge[]) => set({ edges }),
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
    set({
      nodes: get().nodes.filter((node) => node.id !== id),
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
      isActive: workflow.is_active !== false,
    })
  }
}))
