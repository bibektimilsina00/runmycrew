import { useEffect } from 'react'
import { create } from 'zustand'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../stores/editorLayoutStore'
import { editorAPI } from '../services/editorAPI'
import { useToast } from '@/shared/components'
import { useRunsStore } from '@/features/runs/store/runsStore'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { slugifyAppUrl } from '@/features/public-app/utils/slug'

/**
 * Hosted-trigger test loop, shared by every Run button in the editor.
 *
 * Chat App and Form triggers fire per visitor interaction — a bare Run
 * has no payload. Run opens the hosted page (chat or form) and stays
 * "listening": the page posts each execution id back (same-origin
 * postMessage via window.opener) and the log panel attaches to it
 * live, exactly like a webhook trigger's listen mode.
 */
// Keyed by workflow id so navigating to another editor never inherits a
// stale "Listening…" flag. `nodeId` is the hosted trigger node, so the
// canvas can render it as running while the listen is open.
export const useListenState = create<{
  activeFor: string | null
  nodeId: string | null
  set: (workflowId: string | null, nodeId?: string | null) => void
}>(set => ({
  activeFor: null,
  nodeId: null,
  set: (workflowId, nodeId = null) => set({ activeFor: workflowId, nodeId }),
}))

// Both hook instances (action bar + page) register the same message
// listener; process each execution id exactly once.
let lastSeenExecutionId: string | null = null

export function useHostedListen(workflowId: string) {
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const workflow = useWorkflowEditorStore(s => s.workflow)
  const setWorkflow = useWorkflowEditorStore(s => s.setWorkflow)
  const mode = useWorkflowEditorStore(s => s.mode)
  const focusTab = useEditorLayoutStore(s => s.focusTab)
  const wsSlug = useWorkspaceStore(s => s.currentWorkspace?.slug ?? '')
  const { toast } = useToast()

  const hostedNode = nodes.find(
    n => n.type === 'trigger.chat_app' || n.type === 'trigger.form',
  )
  const hasHostedTrigger = Boolean(hostedNode)
  // Shared across hook instances (action bar + page) so every Run button
  // reflects the same listening state.
  const listening = useListenState(s => s.activeFor === workflowId && !!workflowId)
  const setListening = (v: boolean) =>
    useListenState.getState().set(v ? workflowId : null, v ? (hostedNode?.id ?? null) : null)

  useEffect(() => {
    if (!listening || !workflowId) return
    const onMessage = (e: MessageEvent) => {
      if (e.origin !== window.location.origin) return
      const data = e.data as { type?: string; executionId?: string } | null
      if (data?.type !== 'fuse-app-execution' || !data.executionId) return
      if (data.executionId === lastSeenExecutionId) return
      lastSeenExecutionId = data.executionId
      useRunsStore.getState().startRun(workflowId, data.executionId)
      focusTab('logs')
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [listening, workflowId, focusTab])

  const startListening = async () => {
    if (!workflow) return
    // Open the tab synchronously inside the click — awaiting activation
    // first would detach the user gesture and popup blockers eat the
    // window. Navigate it once the page is actually live.
    // (No 'noreferrer': it severs window.opener, which the hosted page
    // uses to post execution ids back. Same-origin page we own — safe.)
    const win = window.open('', '_blank')
    if (!workflow.is_active) {
      try {
        const res = await editorAPI.toggleActive(
          workflowId,
          mode === 'crew' ? 'crew' : 'workflow',
        )
        setWorkflow({ ...workflow, is_active: res.is_active })
      } catch {
        win?.close()
        // Never fail silently — the user pressed Run and saw nothing.
        toast('Could not activate — the hosted page needs the graph live', {
          variant: 'err',
        })
        return
      }
    }
    const props = (hostedNode?.data?.properties ?? {}) as Record<string, unknown>
    const raw = (props.app_slug as string) || (props.title as string) || workflow.name
    const href = `/apps/${wsSlug}/${slugifyAppUrl(raw)}`
    if (win) win.location.href = href
    else window.open(href, '_blank')
    setListening(true)
    toast(
      hostedNode?.type === 'trigger.form'
        ? 'Listening — the graph runs when the form is submitted'
        : 'Listening — each chat message runs the graph live',
      { variant: 'ok' },
    )
  }

  const stopListening = () => setListening(false)

  return { hasHostedTrigger, listening, startListening, stopListening }
}
