import { useCallback, useEffect, useMemo, useState } from 'react'
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

  // ── Fullscreen / Zen Mode ────────────────────────────────────────────────
  const [zenMode, setZenMode] = useState(false)

  // Sync browser fullscreen changes (e.g. user presses Esc)
  useEffect(() => {
    const onFsChange = () => {
      setZenMode(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', onFsChange)
    return () => document.removeEventListener('fullscreenchange', onFsChange)
  }, [])

  const toggleZenMode = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
    } else {
      document.exitFullscreen().catch(() => {})
    }
  }, [])

  // ── Workflow data ────────────────────────────────────────────────────────
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

  const diffActive = useCopilotDiffStore(s => s.active)
  const proposed   = useCopilotDiffStore(s => s.proposed)
  const baseline   = useCopilotDiffStore(s => s.baseline)
  const summary    = useCopilotDiffStore(s => s.summary)

  const canvasNodes = useMemo(() => {
    if (!diffActive || !proposed || !summary || !baseline) return nodes
    const added   = new Set(summary.added)
    const edited  = new Set(summary.edited)
    // className on the React Flow wrapper drives the pop-in keyframe
    // (`.react-flow__node[class*="rf-diff-new"]` in index.css).
    const marked  = proposed.nodes.map(n => {
      const diff = added.has(n.id) ? 'new' : edited.has(n.id) ? 'edited' : undefined
      return {
        ...n,
        className: diff ? `rf-diff-${diff}` : undefined,
        data: { ...n.data, __diff: diff },
      }
    })
    const ghosts  = baseline.nodes
      .filter(n => summary.deleted.includes(n.id))
      .map(n => ({
        ...n,
        draggable: false,
        selectable: false,
        className: 'rf-diff-deleted',
        data: { ...n.data, __diff: 'deleted' },
      }))
    return [...marked, ...ghosts]
  }, [diffActive, proposed, baseline, summary, nodes])

  const canvasEdges = useMemo(() => {
    if (!diffActive || !proposed || !baseline) return edges
    // Edges that exist in proposed but not in baseline → mark new so the
    // stroke-dashoffset keyframe paints them in as they stream.
    const baseKeys = new Set(baseline.edges.map(e => `${e.source}::${e.target}::${e.sourceHandle ?? ''}`))
    return proposed.edges.map(e => {
      const key = `${e.source}::${e.target}::${e.sourceHandle ?? ''}`
      const isNew = !baseKeys.has(key)
      return isNew ? { ...e, className: 'rf-diff-new' } : e
    })
  }, [diffActive, proposed, baseline, edges])

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
      {/* ── Editor shell ─────────────────────────────────────────────── */}
      <div className="relative flex h-full w-full flex-col overflow-hidden">
        {/* Main content area */}
        <div className="relative flex min-h-0 flex-1 overflow-hidden">
          {/* Canvas + Bottom Panel Column */}
          <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
            {/* Canvas */}
            <div className="relative flex min-h-0 flex-1">
              <EditorCanvas
                nodes={canvasNodes}
                edges={canvasEdges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onSelectNode={selectNode}
                interactive={!diffActive}
                onToggleFullscreen={toggleZenMode}
                isFullscreen={zenMode}
              />
            </div>

            {/* Bottom panel */}
            <BottomPanel
              nodes={nodes}
              updateNodeData={updateNodeData}
              onRun={() => run()}
              isRunning={isRunning}
            />
          </div>

          {/* Right panel (expandable sidebar only — no strip) */}
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
