import { useParams, useNavigate } from 'react-router-dom'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkflowEditor } from '../hooks/useWorkflowEditor'
import { EditorCanvas } from '../components/canvas/EditorCanvas'
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
  } = useWorkflowEditor(id ?? '')

  if (isLoading) {
    return <EditorLoading />
  }

  if (error || !workflow) {
    return <EditorError onBack={() => navigate(APP_ROUTES.AUTOMATIONS)} />
  }

  return (
    <div className="flex flex-col h-full w-full bg-[var(--bg)] overflow-hidden">
      <div className="flex flex-1 min-h-0">
        <EditorCanvas
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
        />
      </div>
    </div>
  )
}
