import { useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useReactFlow } from 'reactflow'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'

export interface ActionMenuItem {
  label: string
  icon: string          // lucide icon name — resolved in the UI layer
  onClick: () => void
  variant?: 'danger'
  dividerBefore?: boolean
}

export function useEditorActionBar() {
  const [anchorRect, setAnchorRect] = useState<DOMRect | null>(null)
  const btnRef = useRef<HTMLButtonElement>(null)

  const navigate = useNavigate()
  const { id: workflowId } = useParams<{ id: string }>()
  const { fitView } = useReactFlow()

  const setTab  = useWorkflowEditorStore(s => s.setInspectorTab)
  const nodes   = useWorkflowEditorStore(s => s.nodes)
  const edges   = useWorkflowEditorStore(s => s.edges)

  const openMenu = () => setAnchorRect(btnRef.current?.getBoundingClientRect() ?? null)
  const closeMenu = () => setAnchorRect(null)
  const openCopilot = () => setTab('copilot')

  const exportWorkflow = () => {
    const data = JSON.stringify({ nodes, edges }, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `workflow-${workflowId ?? 'export'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const autoLayout = () => fitView({ duration: 400, padding: 0.2 })

  const deleteWorkflow = () => {
    if (confirm('Delete this workflow? This cannot be undone.')) {
      navigate('/automations')
    }
  }

  return {
    btnRef,
    anchorRect,
    openMenu,
    closeMenu,
    openCopilot,
    exportWorkflow,
    autoLayout,
    deleteWorkflow,
  }
}
