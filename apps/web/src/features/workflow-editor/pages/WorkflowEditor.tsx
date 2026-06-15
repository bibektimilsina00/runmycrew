import { useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ReactFlowProvider } from 'reactflow'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkflowEditor } from '../hooks/useWorkflowEditor'
import { useEditorShortcuts } from '../hooks/useEditorShortcuts'
import { useCopilotDiffStore } from '../stores/copilotDiffStore'
import { useCopilotPendingStore } from '../stores/copilotPendingStore'
import { useEditorLayoutStore } from '../stores/editorLayoutStore'
import { EditorCanvas } from '../components/canvas/EditorCanvas'
import { EditorRightPanel } from '../components/right-panel/EditorRightPanel'
import { BottomPanel } from '../components/bottom-panel/BottomPanel'
import { EditorLoading } from '../components/overlays/EditorLoading'
import { EditorError } from '../components/overlays/EditorError'

export function WorkflowEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  useEditorShortcuts()

  const {
    workflow,
    isLoading,
    error,
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    updateNodeData,
    selectNode,
    run,
    isRunning,
  } = useWorkflowEditor(id ?? '')

  // Copilot diff preview: while a proposal is pending, render the proposed graph
  // (with new/edited/deleted markers) and lock the canvas until Accept/Reject.
  const diffActive = useCopilotDiffStore(s => s.active)
  const proposed = useCopilotDiffStore(s => s.proposed)
  const baseline = useCopilotDiffStore(s => s.baseline)
  const summary = useCopilotDiffStore(s => s.summary)

  const canvasNodes = useMemo(() => {
    if (!diffActive || !proposed || !summary || !baseline) return nodes
    const added = new Set(summary.added)
    const edited = new Set(summary.edited)
    const marked = proposed.nodes.map(n => ({
      ...n,
      data: { ...n.data, __diff: added.has(n.id) ? 'new' : edited.has(n.id) ? 'edited' : undefined },
    }))
    const ghosts = baseline.nodes
      .filter(n => summary.deleted.includes(n.id))
      .map(n => ({ ...n, draggable: false, selectable: false, data: { ...n.data, __diff: 'deleted' } }))
    return [...marked, ...ghosts]
  }, [diffActive, proposed, baseline, summary, nodes])

  const canvasEdges = diffActive && proposed ? proposed.edges : edges

  // If we arrived with a parked prompt (e.g. from the dashboard), focus the
  // Copilot tab in whichever zone hosts it.
  const hasPending = useCopilotPendingStore(s => !!s.prompt)
  useEffect(() => {
    if (hasPending && workflow?.id) {
      useEditorLayoutStore.getState().focusTab('copilot')
    }
  }, [hasPending, workflow?.id])

  if (isLoading) return <EditorLoading />
  if (error || !workflow) return <EditorError onBack={() => navigate(APP_ROUTES.AUTOMATIONS)} />

  return (
    <ReactFlowProvider>
      <div className="flex h-full w-full flex-col overflow-hidden bg-[var(--bg)]">
        <div className="flex min-h-0 flex-1 overflow-hidden">
          <div className="relative flex min-w-0 flex-1">
            <EditorCanvas
              nodes={canvasNodes}
              edges={canvasEdges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onSelectNode={selectNode}
              interactive={!diffActive}
            />
          </div>
          <EditorRightPanel
            nodes={nodes}
            updateNodeData={updateNodeData}
            onRun={() => run()}
            isRunning={isRunning}
          />
        </div>
        <BottomPanel
          nodes={nodes}
          updateNodeData={updateNodeData}
          onRun={() => run()}
          isRunning={isRunning}
        />
      </div>
    </ReactFlowProvider>
  )
}
