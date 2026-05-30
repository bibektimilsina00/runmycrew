import { useMemo } from 'react'
import { useParams, useNavigate, useOutletContext } from 'react-router-dom'
import { ReactFlowProvider } from 'reactflow'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { AppLayoutController } from '@/shared/layouts/app-layout/use-app-layout-controller'
import { useWorkflowEditor } from '../hooks/useWorkflowEditor'
import { useEditorShortcuts } from '../hooks/useEditorShortcuts'
import { useCopilotDiffStore } from '../stores/copilotDiffStore'
import { EditorTopbar } from '../components/topbar/EditorTopbar'
import { EditorCanvas } from '../components/canvas/EditorCanvas'
import { EditorRightPanel } from '../components/right-panel/EditorRightPanel'
import { EditorLoading } from '../components/overlays/EditorLoading'
import { EditorError } from '../components/overlays/EditorError'

export function WorkflowEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const controller = useOutletContext<AppLayoutController>()
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
    rename,
    toggle,
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

  if (isLoading) return <EditorLoading />
  if (error || !workflow) return <EditorError onBack={() => navigate(APP_ROUTES.AUTOMATIONS)} />

  return (
    <ReactFlowProvider>
      <div className="flex h-full w-full flex-col overflow-hidden bg-[var(--bg)]">
        <EditorTopbar
          controller={controller}
          workflowName={workflow.name}
          isActive={workflow.is_active}
          onToggleActive={() => toggle()}
          onRename={(name) => rename(name)}
        />
        <div className="flex min-h-0 flex-1 overflow-hidden">
          <EditorCanvas
            nodes={canvasNodes}
            edges={canvasEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onSelectNode={selectNode}
            interactive={!diffActive}
          />
          <EditorRightPanel
            nodes={nodes}
            updateNodeData={updateNodeData}
            onRun={() => run()}
            isRunning={isRunning}
          />
        </div>
      </div>
    </ReactFlowProvider>
  )
}
