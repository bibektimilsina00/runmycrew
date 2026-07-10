import { useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { useReactFlow } from 'reactflow'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../stores/editorLayoutStore'
import { editorAPI } from '../services/editorAPI'
import { useToast } from '@/shared/components'
import { useRunsStore } from '@/features/runs/store/runsStore'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { slugifyAppUrl } from '@/features/public-app/utils/slug'

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
  const mode        = useWorkflowEditorStore(s => s.mode)
  const { toast }   = useToast()

  // Toggle the deployed state. When active, cron + webhook triggers fire;
  // when paused they're ignored. Crews live in their own table with their
  // own toggle endpoint, so the store's `mode` (set from the /crews/:id
  // route) must ride along — a crew id against the workflows toggle 404s.
  const activateMutation = useMutation({
    mutationFn: () => editorAPI.toggleActive(workflowId ?? '', mode === 'crew' ? 'crew' : 'workflow'),
    onSuccess: (res) => {
      if (workflow) setWorkflow({ ...workflow, is_active: res.is_active })
      const noun = mode === 'crew' ? 'Crew' : 'Workflow'
      toast(res.is_active ? `${noun} activated — triggers are live` : `${noun} paused`, {
        variant: 'ok',
      })
    },
    onError: () => toast('Failed to update state', { variant: 'err' }),
  })

  // ── Chat-trigger test loop ─────────────────────────────────────────
  // A chat_app trigger has no payload to Run with — the graph fires per
  // visitor message. Run therefore opens the hosted page and stays
  // "listening": the chat tab posts each execution id back (same-origin
  // postMessage) and the log panel attaches to it live, exactly like a
  // webhook trigger's listen mode.
  const chatAppNode = nodes.find(n => n.type === 'trigger.chat_app')
  const hasChatAppTrigger = Boolean(chatAppNode)
  const [chatListening, setChatListening] = useState(false)
  const wsSlug = useWorkspaceStore(s => s.currentWorkspace?.slug ?? '')

  useEffect(() => {
    if (!chatListening || !workflowId) return
    const onMessage = (e: MessageEvent) => {
      if (e.origin !== window.location.origin) return
      const data = e.data as { type?: string; executionId?: string } | null
      if (data?.type !== 'fuse-app-execution' || !data.executionId) return
      useRunsStore.getState().startRun(workflowId, data.executionId)
      focusTab('logs')
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [chatListening, workflowId, focusTab])

  const startChatListening = async () => {
    if (!workflow) return
    if (!workflow.is_active) {
      // The hosted page only resolves active graphs — flip it on first.
      await activateMutation.mutateAsync()
    }
    const props = (chatAppNode?.data?.properties ?? {}) as Record<string, unknown>
    const raw = (props.app_slug as string) || (props.title as string) || workflow.name
    // No 'noreferrer': it severs window.opener, which the chat tab uses
    // to post execution ids back. Same-origin page we own — safe.
    window.open(`/apps/${wsSlug}/${slugifyAppUrl(raw)}`, '_blank')
    setChatListening(true)
    toast('Listening — each chat message runs the graph live', { variant: 'ok' })
  }

  const stopChatListening = () => setChatListening(false)

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
    hasChatAppTrigger,
    chatListening,
    startChatListening,
    stopChatListening,
  }
}
