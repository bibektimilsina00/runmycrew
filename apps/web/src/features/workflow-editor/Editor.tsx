import React, { useRef, useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import ReactFlow, {
  ReactFlowProvider,
  SelectionMode,
  ConnectionLineType,
  Background
} from 'reactflow'
import 'reactflow/dist/style.css'

import { EditorInspector } from '@/features/workflow-editor/panels/inspector/EditorInspector'
import { EditorLogs } from '@/features/workflow-editor/panels/logs-panel/EditorLogs'
import { WorkflowControls } from '@/features/workflow-editor/controls/WorkflowControls'
import { useWorkflow } from '@/features/workflow-editor/hooks/use-workflow'
import { useAutoSave } from '@/features/workflow-editor/hooks/use-auto-save'
import { useWorkflowData } from '@/features/workflow-editor/hooks/use-workflow-data'
import { useResizable } from '@/features/workflow-editor/hooks/use-resizable'
import { useNodes } from '@/hooks/nodes/queries'
import { useWorkflowStore } from '@/stores/workflow-store'

import { CustomNode } from '@/features/workflow-editor/nodes/CustomNode'
import { ConditionNode } from '@/features/workflow-editor/nodes/ConditionNode'
import { LoopNode } from '@/features/workflow-editor/nodes/LoopNode'

const MIN_PANEL_WIDTH = 280
const MAX_PANEL_WIDTH = 600
const DEFAULT_PANEL_WIDTH = 320

export default function Editor() {
  const { isLoading, error } = useWorkflowData()
  const [panelWidth, setPanelWidth] = useState(DEFAULT_PANEL_WIDTH)
  const containerRef = useRef<HTMLDivElement>(null)

  const inspectorResizer = useResizable({
    direction: 'horizontal',
    minSize: MIN_PANEL_WIDTH,
    maxSize: MAX_PANEL_WIDTH,
    onSizeChange: setPanelWidth,
    containerRef: containerRef as React.RefObject<HTMLElement>,
    invert: true
  })

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[var(--bg)]">
        <div className="size-8 animate-spin rounded-full border-2 border-[var(--text-muted)] border-t-[var(--text-primary)]" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center bg-[var(--bg)] text-center">
        <p className="mb-4 text-red-500">Failed to load workflow</p>
        <button 
          onClick={() => window.location.reload()}
          className="rounded-lg bg-[var(--surface-3)] px-4 py-2 text-[13px] text-white hover:bg-[var(--surface-hover)]"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <ReactFlowProvider>
      <div
        ref={containerRef}
        className="h-full w-full overflow-hidden bg-[var(--bg)]"
        style={{ display: 'grid', gridTemplateColumns: `minmax(0, 1fr) 5px ${panelWidth}px` }}
      >
        <EditorContent />
        <div
          {...inspectorResizer}
          className="cursor-col-resize select-none z-50 h-full"
        />
        <EditorInspector className="overflow-hidden" />
      </div>
    </ReactFlowProvider>
  )
}


function EditorContent() {
  useAutoSave()
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    onNodeClick,
    onNodeDrag,
    onNodeDragStop,
    onDragOver,
    onDrop,
    reactFlowWrapper,
    mode,
    setMode,
  } = useWorkflow()

  const { data: nodeRegistry = [] } = useNodes()
  const setNodeDefinitions = useWorkflowStore(s => s.setNodeDefinitions)
  const nodeDefinitions = useWorkflowStore(s => s.nodeDefinitions)
  const location = useLocation()

  React.useEffect(() => {
    if (nodeRegistry.length > 0) {
      setNodeDefinitions(nodeRegistry)
    }
  }, [nodeRegistry, setNodeDefinitions])

  // Auto-open Copilot tab and send prompt when navigated from a template
  useEffect(() => {
    const autoPrompt = (location.state as any)?.autoPrompt
    if (!autoPrompt) return
    const { setInspectorTab, setCopilotAutoPrompt } = require('@/stores/ui-store').useUIStore.getState()
    setInspectorTab('Copilot')
    setCopilotAutoPrompt(autoPrompt)
    // Clear location state so refresh doesn't re-trigger
    window.history.replaceState({}, '')
  }, [location.state])

  // Build nodeTypes from API response — all non-condition types use CustomNode.
  // Memoized: only rebuilds when nodeDefinitions change (rare after first load).
  const nodeTypes = React.useMemo(() => {
    const types: Record<string, React.ComponentType<any>> = {
      'logic.condition': ConditionNode,
      'logic.loop': LoopNode,
    }
    for (const def of nodeDefinitions) {
      if (!types[def.type]) types[def.type] = CustomNode
    }
    return types
  }, [nodeDefinitions])

  const [connectionColor, setConnectionColor] = React.useState('var(--workflow-edge, #555)')

  const onConnectStart = React.useCallback((_: any, { handleId }: any) => {
    if (handleId === 'error') {
      setConnectionColor('#ff4d4f')
    } else {
      setConnectionColor('var(--workflow-edge, #555)')
    }
  }, [])

  const onConnectEnd = React.useCallback(() => {
    setConnectionColor('var(--workflow-edge)')
  }, [])

  // Wait for node definitions from API before rendering ReactFlow.
  // Without them nodeTypes is empty and ReactFlow logs #003 for every node type.
  if (nodeDefinitions.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-[var(--bg)]">
        <div className="size-8 animate-spin rounded-full border-2 border-[var(--text-muted)] border-t-[var(--text-primary)]" />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col min-w-0 bg-[var(--bg)] relative overflow-hidden">
      <div className="flex-1 relative" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onDragOver={onDragOver}
          onDrop={onDrop}
          onNodeDrag={onNodeDrag}
          onNodeDragStop={onNodeDragStop}
          onConnectStart={onConnectStart}
          onConnectEnd={onConnectEnd}
          defaultEdgeOptions={{
            type: 'smoothstep',
            style: { strokeWidth: 2 }
          }}
          connectionLineType={ConnectionLineType.SmoothStep}
          connectionLineStyle={{
            stroke: connectionColor,
            strokeWidth: 2,
            transition: 'stroke 0.2s ease'
          }}
          panOnDrag={mode === 'pan'}
          selectionOnDrag={mode === 'select'}
          panOnScroll={mode === 'select'}
          selectionMode={mode === 'select' ? SelectionMode.Full : SelectionMode.Partial}
          fitView
          fitViewOptions={{ maxZoom: 0.8, padding: 0.2 }}
          defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
          snapToGrid={false}
          snapGrid={[10, 10]}
          style={{ background: 'var(--bg)' }}
        >
          <Background color="#222" gap={20} />
        </ReactFlow>
        <WorkflowControls mode={mode} onModeChange={setMode} />
      </div>
      <EditorLogs />
    </div>
  )
}
