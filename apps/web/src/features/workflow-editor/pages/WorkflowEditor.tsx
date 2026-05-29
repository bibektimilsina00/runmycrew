import { useParams, useNavigate, useOutletContext } from 'react-router-dom'
import { ReactFlowProvider } from 'reactflow'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { AppLayoutController } from '@/shared/layouts/app-layout/use-app-layout-controller'
import { useWorkflowEditor } from '../hooks/useWorkflowEditor'
import { useEditorShortcuts } from '../hooks/useEditorShortcuts'
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
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onSelectNode={selectNode}
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
