import { useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useOnSelectionChange, useReactFlow } from 'reactflow'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import { useCollaborationLifecycle, useCollaborationSenders } from './useCollaboration'
import { useCollaborationStore } from './collaborationStore'
import { PeerCursors } from './components/PeerCursors'
import { PeerSelectionStyles } from './components/PeerSelectionStyles'

/**
 * Drop-in shell that wires the WebSocket lifecycle to the React Flow
 * canvas. Mount it inside `<ReactFlowProvider>` so `useReactFlow()`
 * resolves and we can convert pointer events to canvas coordinates.
 *
 * Why a separate component instead of putting this in WorkflowEditor?
 * `useReactFlow()` only works inside the provider — the editor mounts
 * the provider in its render tree, so this layer has to live a level
 * below. Keeping the hook + UI together also means the collab feature
 * has exactly one mount point.
 */
const CURSOR_THROTTLE_MS = 40 // ~25 fps — smooth without flooding Redis
const GRAPH_PATCH_DEBOUNCE_MS = 300 // edits settle before broadcasting

export function CollaborationLayer() {
  const { id: workflowId } = useParams<{ id: string }>()
  useCollaborationLifecycle(workflowId)
  const { sendCursor, sendSelection, sendGraphPatch } = useCollaborationSenders()
  const { screenToFlowPosition } = useReactFlow()
  const lastSentRef = useRef(0)

  // Subscribe to local graph changes and broadcast a debounced patch.
  // The first render after mount is skipped because there's no "edit"
  // to share, and a brief window after applying a remote patch is
  // skipped via `applyingRemoteUntil` (set by the receive handler).
  const nodes = useWorkflowEditorStore((s) => s.nodes)
  const edges = useWorkflowEditorStore((s) => s.edges)
  const isFirstRunRef = useRef(true)
  useEffect(() => {
    if (!workflowId) return
    if (isFirstRunRef.current) {
      isFirstRunRef.current = false
      return
    }
    const timer = setTimeout(() => {
      const { applyingRemoteUntil } = useCollaborationStore.getState()
      if (performance.now() < applyingRemoteUntil) return
      sendGraphPatch({ nodes, edges })
    }, GRAPH_PATCH_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [nodes, edges, workflowId, sendGraphPatch])

  useEffect(() => {
    if (!workflowId) return
    const onPointerMove = (ev: PointerEvent) => {
      const now = performance.now()
      if (now - lastSentRef.current < CURSOR_THROTTLE_MS) return
      lastSentRef.current = now
      const flowPos = screenToFlowPosition({ x: ev.clientX, y: ev.clientY })
      sendCursor(flowPos)
    }
    window.addEventListener('pointermove', onPointerMove)
    return () => window.removeEventListener('pointermove', onPointerMove)
  }, [workflowId, sendCursor, screenToFlowPosition])

  // React Flow batches selection changes through this hook so we don't
  // need to add an `onSelectionChange` prop to every place ReactFlow is
  // instantiated. Fires once per selection event with both selected
  // nodes + edges.
  useOnSelectionChange({
    onChange: ({ nodes }) => {
      if (!workflowId) return
      sendSelection(nodes.map((n) => n.id))
    },
  })

  return (
    <>
      <PeerSelectionStyles />
      <PeerCursors />
    </>
  )
}
