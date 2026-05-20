import React, { useRef, useState, useEffect, useCallback } from 'react'
import { computeDAGLayout } from '@/features/workflow-editor/utils/node-placement'
import { useLocation } from 'react-router-dom'
import ReactFlow, {
  ReactFlowProvider,
  SelectionMode,
  ConnectionLineType,
  Background,
  useReactFlow,
} from 'reactflow'
import 'reactflow/dist/style.css'

import { EditorInspector } from '@/features/workflow-editor/panels/inspector/EditorInspector'
import { EditorLogs } from '@/features/workflow-editor/panels/logs-panel/EditorLogs'
import { WorkflowControls } from '@/features/workflow-editor/controls/WorkflowControls'
import { CollaborationOverlay } from '@/features/workflow-editor/components/CollaborationOverlay'
import { ContextMenu, NODE_CONTEXT_ITEMS, PANE_CONTEXT_ITEMS } from '@/features/workflow-editor/components/context-menu/ContextMenu'
import { useWorkflow } from '@/features/workflow-editor/hooks/use-workflow'
import { useAutoSave } from '@/features/workflow-editor/hooks/use-auto-save'
import { useWorkflowData } from '@/features/workflow-editor/hooks/use-workflow-data'
import { useWorkflowCollaboration } from '@/features/workflow-editor/hooks/use-workflow-collaboration'
import { useResizable } from '@/features/workflow-editor/hooks/use-resizable'
import { useNodes } from '@/hooks/nodes/queries'
import { useWorkflowStore } from '@/stores/workflow-store'
import { useUIStore } from '@/stores/ui-store'

import { CustomNode } from '@/features/workflow-editor/nodes/CustomNode'
import { CustomEdge } from '@/features/workflow-editor/edges/CustomEdge'
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
    onNodeContextMenu,
    onPaneContextMenu,
    contextMenu,
    closeContextMenu,
    removeNode,
    duplicateNode,
    toggleNodeLock,
    toggleNodeDisabled,
    startNodeRename,
    selectAllNodes,
    setSearchOpen,
    reactFlowWrapper,
    mode,
    setMode,
  } = useWorkflow()
  const workflowId = useWorkflowStore(s => s.workflowId)
  const selectedNodeId = useWorkflowStore(s => s.selectedNodeId)
  const collaboration = useWorkflowCollaboration(workflowId)

  const { fitView, setNodes: rfSetNodes, screenToFlowPosition, getViewport } = useReactFlow()
  const setNodesStore = useWorkflowStore(s => s.setNodes)

  const runAutoLayout = useCallback(() => {
    const rootNodes = nodes.filter(n => !n.parentNode)
    const positions = computeDAGLayout(rootNodes, edges)
    if (positions.size === 0) { fitView({ duration: 400, padding: 0.2 }); return }
    setNodesStore(prev => prev.map(n => {
      const pos = positions.get(n.id)
      return pos ? { ...n, position: pos } : n
    }))
    setTimeout(() => fitView({ duration: 400, padding: 0.2 }), 50)
  }, [nodes, edges, setNodesStore, fitView])
  const { data: nodeRegistry = [] } = useNodes()
  const setNodeDefinitions = useWorkflowStore(s => s.setNodeDefinitions)
  const nodeDefinitions = useWorkflowStore(s => s.nodeDefinitions)
  const workflowLocked = useWorkflowStore(s => s.workflowLocked)
  const undo = useWorkflowStore(s => s.undo)
  const redo = useWorkflowStore(s => s.redo)

  // Undo / redo keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const meta = e.metaKey || e.ctrlKey
      if (!meta) return
      // Don't fire when typing in inputs
      const tag = (e.target as HTMLElement).tagName
      if (['INPUT', 'TEXTAREA'].includes(tag)) return

      if (e.key === 'z' && !e.shiftKey) { e.preventDefault(); undo() }
      if ((e.key === 'z' && e.shiftKey) || e.key === 'y') { e.preventDefault(); redo() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [undo, redo])

  useEffect(() => {
    collaboration.sendSelection(selectedNodeId)
  }, [collaboration, selectedNodeId])
  const { setInspectorTab: switchTab } = useUIStore()
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

  const edgeTypes = React.useMemo(() => ({ custom: CustomEdge }), [])

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
      <div
        className="flex-1 relative"
        ref={reactFlowWrapper}
        onMouseMove={event => {
          // Convert screen coords → flow coords so cursors align correctly at any zoom/pan
          const flowPos = screenToFlowPosition({ x: event.clientX, y: event.clientY })
          const vp = getViewport()
          collaboration.sendCursor({ x: flowPos.x, y: flowPos.y, viewport: vp })
        }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onDragOver={onDragOver}
          onDrop={onDrop}
          onNodeDrag={onNodeDrag}
          onNodeDragStop={(event, node) => {
            onNodeDragStop(event, node)
            collaboration.sendNodePosition(node)
          }}
          onNodeContextMenu={onNodeContextMenu}
          onPaneContextMenu={onPaneContextMenu}
          onConnectStart={onConnectStart}
          onConnectEnd={onConnectEnd}
          defaultEdgeOptions={{
            type: 'custom',
            style: { strokeWidth: 2 }
          }}
          connectionLineType={ConnectionLineType.SmoothStep}
          connectionLineStyle={{
            stroke: connectionColor,
            strokeWidth: 2,
            transition: 'stroke 0.2s ease'
          }}
          nodesDraggable={!workflowLocked}
          nodesConnectable={!workflowLocked}
          elementsSelectable={!workflowLocked}
          panOnDrag={workflowLocked ? true : mode === 'pan'}
          selectionOnDrag={!workflowLocked && mode === 'select'}
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
        <CollaborationOverlay />
        <WorkflowControls mode={mode} onModeChange={setMode} />
      </div>
      <EditorLogs />

      {/* Node context menu */}
      {contextMenu?.type === 'node' && contextMenu.nodeId && (() => {
        const node = nodes.find(n => n.id === contextMenu.nodeId)
        return (
          <ContextMenu
            x={contextMenu.x}
            y={contextMenu.y}
            onClose={closeContextMenu}
            items={NODE_CONTEXT_ITEMS({
              nodeId: contextMenu.nodeId,
              isLocked: node?.data?.locked ?? false,
              isDisabled: node?.data?.disabled ?? false,
              onDuplicate: () => duplicateNode(contextMenu.nodeId!),
              onDisableToggle: () => toggleNodeDisabled(contextMenu.nodeId!),
              onFlipHandles: () => {
                const n = nodes.find(x => x.id === contextMenu.nodeId)
                if (n) toggleNodeLock(contextMenu.nodeId!) // reuse — or add flip action
              },
              onLockToggle: () => toggleNodeLock(contextMenu.nodeId!),
              onRename: () => startNodeRename(contextMenu.nodeId!),
              onOpenEditor: () => { switchTab('Editor') },
              onDelete: () => removeNode(contextMenu.nodeId!),
            })}
          />
        )
      })()}

      {/* Pane context menu */}
      {contextMenu?.type === 'pane' && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          onClose={closeContextMenu}
          items={PANE_CONTEXT_ITEMS({
            onUndo: () => {},
            onRedo: () => {},
            onAddNode: () => setSearchOpen(true),
            onAutoLayout: runAutoLayout,
            onFitView: () => fitView({ duration: 300, padding: 0.15 }),
            onOpenLogs: () => switchTab('Editor'),
            onOpenChat: () => switchTab('Copilot'),
            canUndo: false,
            canRedo: false,
          })}
        />
      )}
    </div>
  )
}
