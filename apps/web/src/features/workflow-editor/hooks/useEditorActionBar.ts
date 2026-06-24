import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { useReactFlow } from 'reactflow'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../stores/editorLayoutStore'
import { editorAPI } from '../services/editorAPI'
import { useToast } from '@/shared/components'

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

  const focusTab    = useEditorLayoutStore(s => s.focusTab)
  const toggleZone  = useEditorLayoutStore(s => s.toggleZone)
  const nodes       = useWorkflowEditorStore(s => s.nodes)
  const edges       = useWorkflowEditorStore(s => s.edges)
  const workflow    = useWorkflowEditorStore(s => s.workflow)
  const setWorkflow = useWorkflowEditorStore(s => s.setWorkflow)
  const { toast }   = useToast()

  // Toggle the workflow's deployed state. When active, cron + webhook
  // triggers fire; when paused they're ignored. The editor's Activate
  // button is a thin wrapper over this mutation so the user can deploy
  // without leaving the canvas.
  const activateMutation = useMutation({
    mutationFn: () => editorAPI.toggleActive(workflowId ?? ''),
    onSuccess: (res) => {
      if (workflow) setWorkflow({ ...workflow, is_active: res.is_active })
      toast(res.is_active ? 'Workflow activated — triggers are live' : 'Workflow paused', {
        variant: 'ok',
      })
    },
    onError: () => toast('Failed to update workflow state', { variant: 'err' }),
  })

  const openMenu = () => setAnchorRect(btnRef.current?.getBoundingClientRect() ?? null)
  const closeMenu = () => setAnchorRect(null)
  const openCopilot = () => focusTab('copilot')
  const collapseRightPanel = () => toggleZone('right')

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
    collapseRightPanel,
    isActive: !!workflow?.is_active,
    isToggling: activateMutation.isPending,
    toggleActive: () => activateMutation.mutate(),
  }
}
