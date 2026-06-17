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
  //
  // Two modes:
  //
  //   - Workflows whose first node is a Meta trigger use the listen-slot
  //     path: the editor opens a "Listen for next event" slot, the run
  //     row sits in `waiting` until a real webhook lands, and the canvas
  //     animates the real event end-to-end. Matches n8n's debug UX.
  //
  //   - All other workflows (manual triggers, action-only graphs,
  //     non-Meta triggers) fall through to the existing `/run` path
  //     which dispatches immediately with whatever `trigger_data` the
  //     fixture replay (or empty payload) provides.
  //
  // The choice is made at click-time off the live graph so a user
  // doesn't need to know which mode they're in.
  // Trigger node types that need the `/listen` endpoint instead of the
  // fire-once `/run` endpoint. Meta triggers wait on real webhooks;
  // polling triggers (Gmail / Calendar / …) wait on a Celery-driven
  // snapshot-then-poll loop. Either way the editor should open the
  // listen slot when the user clicks Run on a graph containing one.
  const POLLING_LISTEN_TYPES = new Set([
    'trigger.gmail',
    'trigger.gcal_event',
    'trigger.gdrive_change',
    'trigger.google_sheets',
    'trigger.gtasks_change',
    'trigger.gforms_response',
    'trigger.gpeople_change',
  ])

  const hasMetaTrigger = useCallback(() => {
    const { nodes } = useWorkflowEditorStore.getState()
    return nodes.some(
      (n) =>
        typeof n.type === 'string' &&
        (n.type.startsWith('trigger.meta.') || POLLING_LISTEN_TYPES.has(n.type)),
    )
  }, [])

  const runMutation = useMutation({
    mutationFn: async () => {
      if (hasMetaTrigger()) {
        const res = await editorAPI.listen(workflowId)
        return {
          execution_id: res.execution_id,
          waiting_for: res.waiting_for,
          node_id: res.node_id,
          target_id: res.target_id,
          ttl_seconds: res.ttl_seconds,
          mode: 'listen' as const,
        }
      }
      const res = await editorAPI.run(workflowId)
      return {
        execution_id: res.execution_id,
        waiting_for: null,
        node_id: null,
        target_id: null,
        ttl_seconds: null,
        mode: 'run' as const,
      }
    },
    onSuccess: (res) => {
      const runs = useRunsStore.getState()
      if (res.mode === 'listen' && res.waiting_for) {
        runs.startListen(workflowId, res.execution_id, res.waiting_for, {
          nodeId: res.node_id ?? undefined,
          targetId: res.target_id ?? undefined,
          ttlSeconds: res.ttl_seconds ?? undefined,
        })
      } else {
        runs.setActiveExecutionId(workflowId, res.execution_id)
      }
      focusTab('logs')
    },
    onError: (err: unknown) => {
      // Surface the API failure in the Logs panel so users see *why* their
      // Run/Listen click didn't open a slot, instead of an empty
      // "Run the workflow to see execution logs here" state.
      const e = err as { detail?: string; message?: string; status?: number } | undefined
      const detail = e?.detail || e?.message || 'Run failed'
      const status = e?.status ? ` (HTTP ${e.status})` : ''
      // Attach the failure to the offending trigger node so it renders as
      // a normal node-failure row + clicking it shows ErrorView on the right.
      // For Meta /listen the failure is always at the trigger; for plain /run
      // fall back to the first node so the user still gets a clickable entry.
      const { nodes } = useWorkflowEditorStore.getState()
      const triggerNode =
        nodes.find((n) => typeof n.type === 'string' && n.type.startsWith('trigger.meta.')) ??
        nodes.find((n) => typeof n.type === 'string' && n.type.startsWith('trigger.')) ??
        nodes[0]
      if (!triggerNode) return
      useRunsStore
        .getState()
        .recordRunFailure(workflowId, `${detail}${status}`, triggerNode.id)
      focusTab('logs')
    },
  })

  const cancelListenMutation = useMutation({
    mutationFn: (nodeId: string) => editorAPI.cancelListen(workflowId, nodeId),
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
    cancelListen: cancelListenMutation.mutate,
    rename: renameMutation.mutate,
    toggle: toggleMutation.mutate,
    isRunning: runMutation.isPending,
    saveState,
  }
}
