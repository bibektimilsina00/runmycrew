import { useEffect, useCallback, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { addEdge, type Connection, type Edge, type Node } from 'reactflow'
import type { ApiNodeDefinition, NodeDefinition } from '../types/editorTypes'

import { editorAPI } from '../services/editorAPI'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../stores/editorLayoutStore'
import { useRunsStore } from '@/features/runs/store/runsStore'
import { renameNodeInGraph } from '../utils/rename-refactor'

const AUTOSAVE_DELAY = 1500 // ms

interface SavedGraph {
  nodes: Pick<Node, 'id' | 'type' | 'position' | 'data'>[]
  edges: Pick<Edge, 'id' | 'source' | 'target' | 'sourceHandle' | 'targetHandle' | 'type'>[]
}

// Persisted graph — only durable fields. Strips volatile ReactFlow state
// (selected, dragging, measured width/height) so selecting/measuring a node
// doesn't dirty the graph and trigger a redundant autosave.
function cleanGraph(nodes: Node[], edges: Edge[]): SavedGraph {
  return {
    nodes: nodes.map(n => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
    edges: edges.map(e => ({
      id: e.id, source: e.source, target: e.target,
      sourceHandle: e.sourceHandle, targetHandle: e.targetHandle, type: e.type,
    })),
  }
}

function conflictVersion(err: unknown): number | undefined {
  const detail = (err as { response?: { data?: { detail?: { current_version?: number } } } })
    .response?.data?.detail
  return typeof detail?.current_version === 'number' ? detail.current_version : undefined
}

function normalizeDefinition(d: ApiNodeDefinition): NodeDefinition {
  return {
    ...d,
    allowError: d.allow_error,
    outputsSchema: d.outputs_schema,
    credentialType: (d.credential_type as string | undefined) ?? undefined,
  }
}

export function useWorkflowEditor(workflowId: string) {
  const storeWorkflow = useWorkflowEditorStore(s => s.workflow)
  const saveState = useWorkflowEditorStore(s => s.saveState)
  const setWorkflow = useWorkflowEditorStore(s => s.setWorkflow)
  const setNodeDefinitions = useWorkflowEditorStore(s => s.setNodeDefinitions)
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const edges = useWorkflowEditorStore(s => s.edges)
  const setNodes = useWorkflowEditorStore(s => s.setNodes)
  const setEdges = useWorkflowEditorStore(s => s.setEdges)
  const onNodesChange = useWorkflowEditorStore(s => s.onNodesChange)
  const onEdgesChange = useWorkflowEditorStore(s => s.onEdgesChange)
  const pushHistory = useWorkflowEditorStore(s => s.pushHistory)
  const setSaveState = useWorkflowEditorStore(s => s.setSaveState)
  const setVersionVector = useWorkflowEditorStore(s => s.setVersionVector)
  const setSelectedNodeId = useWorkflowEditorStore(s => s.setSelectedNodeId)
  const focusTab = useEditorLayoutStore(s => s.focusTab)
  const resetEditorStore = useWorkflowEditorStore(s => s.reset)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastSavedKey = useRef<string>('')   // serialized graph last persisted
  const lastAttempt = useRef<SavedGraph | null>(null)
  const retrying = useRef(false)

  // ── Fetch node definitions (shared, long-lived cache) ─────────────────────
  const { data: rawDefinitions } = useQuery({
    queryKey: ['node-definitions'],
    queryFn: ({ signal }) => editorAPI.getNodeDefinitions(signal),
    staleTime: 1000 * 60 * 10, // 10 min
  })

  useEffect(() => {
    if (rawDefinitions && rawDefinitions.length > 0) {
      setNodeDefinitions(rawDefinitions.map(normalizeDefinition))
    }
  }, [rawDefinitions, setNodeDefinitions])

  // ── Fetch workflow ────────────────────────────────────────────────────────
  const { data: workflow, isLoading, error } = useQuery({
    queryKey: ['workflow-editor', workflowId],
    queryFn: ({ signal }) => editorAPI.getWorkflow(workflowId, signal),
    staleTime: Infinity, // editor owns the data
  })

  // Populate the store graph when the workflow loads
  useEffect(() => {
    if (!workflow) return
    setWorkflow(workflow)
    setVersionVector(workflow.version_vector ?? 0)

    const graph = workflow.graph ?? { nodes: [], edges: [] }
    const loadedNodes: Node[] = graph.nodes ?? []
    const loadedEdges: Edge[] = (graph.edges ?? []).map((e: Edge) => ({ ...e, type: 'custom' }))
    setNodes(loadedNodes)
    setEdges(loadedEdges)
    // Mark the loaded graph as already-saved so hydration doesn't autosave.
    lastSavedKey.current = JSON.stringify(cleanGraph(loadedNodes, loadedEdges))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflow?.id])

  // ── Auto-save ─────────────────────────────────────────────────────────────
  const saveMutation = useMutation({
    mutationFn: ({ graph, version }: { graph: SavedGraph; version: number }) =>
      editorAPI.saveGraph(workflowId, graph, version),
    onMutate: () => setSaveState('saving'),
    onSuccess: (updated) => {
      retrying.current = false
      setSaveState('saved')
      setVersionVector(updated.version_vector ?? 0)
      if (lastAttempt.current) lastSavedKey.current = JSON.stringify(lastAttempt.current)
    },
    onError: (err) => {
      // Optimistic-concurrency conflict: adopt the server version and retry once
      // (single-user editor → last-write-wins). Prevents an endless 409 loop.
      const current = conflictVersion(err)
      if (current !== undefined) {
        setVersionVector(current)
        if (!retrying.current && lastAttempt.current) {
          retrying.current = true
          saveMutation.mutate({ graph: lastAttempt.current, version: current })
          return
        }
      }
      retrying.current = false
      setSaveState('error')
    },
  })

  const triggerSave = useCallback((newNodes: Node[], newEdges: Edge[]) => {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    setSaveState('unsaved')
    saveTimer.current = setTimeout(() => {
      const graph = cleanGraph(newNodes, newEdges)
      lastAttempt.current = graph
      saveMutation.mutate({ graph, version: useWorkflowEditorStore.getState().versionVector })
    }, AUTOSAVE_DELAY)
  }, [saveMutation, setSaveState])

  // Autosave when the durable graph changes (skips hydration + selection-only changes)
  useEffect(() => {
    if (!workflow) return
    const key = JSON.stringify(cleanGraph(nodes, edges))
    if (key === lastSavedKey.current) return
    triggerSave(nodes, edges)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges])

  const updateNodeData = useCallback((nodeId: string, data: Record<string, unknown>) => {
    setNodes(currentNodes =>
      currentNodes.map(node =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...data } }
          : node,
      ),
    )
  }, [setNodes])

  /**
   * Rename a node's display label and atomically rewrite every
   * `$node('Old')` reference in every other node's properties to
   * `$node('New')`. The rewrite + label-set happen in a single setNodes
   * batch so callers never see a half-renamed graph.
   */
  const renameNode = useCallback((nodeId: string, newLabel: string) => {
    setNodes(currentNodes => renameNodeInGraph(currentNodes, nodeId, newLabel))
  }, [setNodes])

  const onConnect = useCallback((connection: Connection) => {
    pushHistory()
    setEdges(eds => addEdge({
      ...connection,
      type: 'custom',
      animated: false,
      style: { stroke: 'var(--border)', strokeWidth: 2 },
    }, eds))
  }, [setEdges, pushHistory])

  // Only open inspector on explicit node click — never clear on deselect
  const selectNode = useCallback((nodeId: string) => {
    const current = useWorkflowEditorStore.getState()
    if (current.selectedNodeId !== nodeId) setSelectedNodeId(nodeId)
    focusTab('config')
  }, [setSelectedNodeId, focusTab])

  // ── Run ───────────────────────────────────────────────────────────────────
  const runMutation = useMutation({
    mutationFn: () => editorAPI.run(workflowId),
    onSuccess: (res) => {
      useRunsStore.getState().setActiveExecutionId(workflowId, res.execution_id)
      focusTab('logs')
    },
  })

  // ── Rename ────────────────────────────────────────────────────────────────
  const renameMutation = useMutation({
    mutationFn: (name: string) => editorAPI.rename(workflowId, name),
    onSuccess: (updated) => setWorkflow(updated),
  })

  // ── Toggle active ─────────────────────────────────────────────────────────
  const toggleMutation = useMutation({
    mutationFn: () => editorAPI.toggleActive(workflowId),
    onSuccess: (res) => {
      if (storeWorkflow) setWorkflow({ ...storeWorkflow, is_active: res.is_active })
    },
  })

  // Cleanup on unmount
  useEffect(() => () => {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    resetEditorStore()
  }, [resetEditorStore])

  return {
    workflow,
    isLoading,
    error,
    // Graph
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    setNodes,
    setEdges,
    updateNodeData,
    renameNode,
    selectNode,
    // Actions
    run: runMutation.mutate,
    rename: renameMutation.mutate,
    toggle: toggleMutation.mutate,
    isRunning: runMutation.isPending,
    saveState,
  }
}
