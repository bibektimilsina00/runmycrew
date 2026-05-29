import { useParams, useNavigate } from 'react-router-dom'
import { ReactFlowProvider } from 'reactflow'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkflowEditor } from '../hooks/useWorkflowEditor'
import { EditorCanvas } from '../components/canvas/EditorCanvas'
import { EditorRightPanel } from '../components/right-panel/EditorRightPanel'
import { EditorLoading } from '../components/overlays/EditorLoading'
import { EditorError } from '../components/overlays/EditorError'

export function WorkflowEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

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

  if (isLoading) return <EditorLoading />
  if (error || !workflow) return <EditorError onBack={() => navigate(APP_ROUTES.AUTOMATIONS)} />

  return (
    <ReactFlowProvider>
    <div className="flex h-full w-full overflow-hidden bg-[var(--bg)]">
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
    </ReactFlowProvider>
  )
}
