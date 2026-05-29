import { useCallback, useMemo, useState } from 'react'
import ReactFlow, {
  Background,
  BackgroundVariant,
  ConnectionLineType,
  useReactFlow,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useShallow } from 'zustand/react/shallow'
import { buildNodeTypes } from '../../constants/nodeTypes'
import { CustomEdge } from '../edges/CustomEdge'
import { ContextMenu, type ContextMenuItem } from '../context-menu/ContextMenu'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'

const edgeTypes = { custom: CustomEdge }

interface Props {
  nodes: Node[]
  edges: Edge[]
  onNodesChange: OnNodesChange
  onEdgesChange: OnEdgesChange
  onConnect?: OnConnect
  onSelectNode?: (nodeId: string) => void
}

interface MenuState {
  type: 'node' | 'pane'
  x: number
  y: number
  nodeId?: string
}

function Flow({ nodes, edges, onNodesChange, onEdgesChange, onConnect, onSelectNode }: Props) {
  const nodeDefinitions = useWorkflowEditorStore(useShallow(s => s.nodeDefinitions))
  const setInspectorTab = useWorkflowEditorStore(s => s.setInspectorTab)
  const setNodes = useWorkflowEditorStore(s => s.setNodes)
  const pushHistory = useWorkflowEditorStore(s => s.pushHistory)
  const { screenToFlowPosition, fitView } = useReactFlow()
  const [menu, setMenu] = useState<MenuState | null>(null)

  // Computed once after definitions load — never changes reference after first mount.
  const nodeTypes = useMemo(() => buildNodeTypes(nodeDefinitions), [nodeDefinitions])

  const handleConnect: OnConnect = useCallback(
    (connection) => { if (onConnect) onConnect(connection) },
    [onConnect],
  )

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const type = e.dataTransfer.getData('application/reactflow')
    if (!type) return
    const def = nodeDefinitions.find(d => d.type === type)
    if (!def) return
    const position = screenToFlowPosition({ x: e.clientX, y: e.clientY })
    pushHistory()
    setNodes(ns => [...ns, {
      id: crypto.randomUUID(),
      type,
      position,
      data: { label: def.name, properties: {} },
    }])
  }, [nodeDefinitions, screenToFlowPosition, setNodes, pushHistory])

  const onNodeContextMenu = useCallback((e: React.MouseEvent, node: Node) => {
    e.preventDefault()
    setMenu({ type: 'node', x: e.clientX, y: e.clientY, nodeId: node.id })
  }, [])

  const onPaneContextMenu = useCallback((e: React.MouseEvent | MouseEvent) => {
    e.preventDefault()
    setMenu({ type: 'pane', x: e.clientX, y: e.clientY })
  }, [])

  const onNodeDragStart = useCallback(() => pushHistory(), [pushHistory])

  const buildMenuItems = (): ContextMenuItem[] => {
    const s = useWorkflowEditorStore.getState()
    if (menu?.type === 'node' && menu.nodeId) {
      const id = menu.nodeId
      const locked = (nodes.find(n => n.id === id)?.data?.locked as boolean | undefined) ?? false
      return [
        { label: 'Copy', shortcut: '⌘C', onClick: () => { s.setNodes(ns => ns.map(n => ({ ...n, selected: n.id === id }))); s.copySelection() } },
        { label: 'Duplicate', shortcut: '⌘D', onClick: () => s.duplicateNode(id) },
        { label: locked ? 'Unlock' : 'Lock', onClick: () => s.toggleNodeLock(id) },
        { label: 'Delete', shortcut: '⌫', variant: 'danger', dividerBefore: true, onClick: () => s.removeNode(id) },
      ]
    }
    return [
      { label: 'Paste', shortcut: '⌘V', disabled: !s.clipboard, onClick: () => s.paste() },
      { label: 'Select all', shortcut: '⌘A', onClick: () => s.selectAll() },
      { label: 'Add node', dividerBefore: true, onClick: () => s.setInspectorTab('library') },
      { label: 'Fit view', onClick: () => fitView({ duration: 300, padding: 0.2 }) },
      { label: 'Undo', shortcut: '⌘Z', dividerBefore: true, disabled: !s.past.length, onClick: () => s.undo() },
      { label: 'Redo', shortcut: '⌘⇧Z', disabled: !s.future.length, onClick: () => s.redo() },
    ]
  }

  return (
    <>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={handleConnect}
        onDragOver={onDragOver}
        onDrop={onDrop}
        onNodeClick={(_, node) => onSelectNode?.(node.id)}
        onNodeContextMenu={onNodeContextMenu}
        onPaneContextMenu={onPaneContextMenu}
        onNodeDragStart={onNodeDragStart}
        deleteKeyCode={null}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        connectionLineType={ConnectionLineType.SmoothStep}
        connectionLineStyle={{ stroke: 'var(--border)', strokeWidth: 2 }}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{ type: 'custom', animated: false }}
        proOptions={{ hideAttribution: true }}
        style={{ background: 'var(--bg)' }}
      >
        {/* Dot grid background matching the app design */}
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1}
          color="oklch(0.32 0.004 250)"
          style={{ background: 'var(--bg)' }}
        />

        {/* Empty state overlay */}
        {nodes.length === 0 && (
          <div
            className="absolute inset-0 flex flex-col items-center justify-center gap-3"
            style={{ zIndex: 4 }}
          >
            <button
              onClick={() => setInspectorTab('library')}
              className="flex w-[48px] h-[48px] rounded-[12px] bg-[var(--surface)] border border-[var(--border-faint)] items-center justify-center transition-colors hover:bg-[var(--surface-2)] hover:border-[var(--border-soft)]"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-mute)" strokeWidth="1.5">
                <path d="M12 5v14M5 12h14" strokeLinecap="round" />
              </svg>
            </button>
            <div className="text-center pointer-events-none">
              <p className="text-[13.5px] font-medium text-[var(--text-mute)]">Empty canvas</p>
              <p className="text-[12px] text-[var(--text-faint)] mt-0.5">
                Click <strong className="text-[var(--text-mute)] font-medium">+</strong> to browse nodes, or drag from the Library
              </p>
            </div>
          </div>
        )}
      </ReactFlow>

      {menu && (
        <ContextMenu x={menu.x} y={menu.y} items={buildMenuItems()} onClose={() => setMenu(null)} />
      )}
    </>
  )
}

export function EditorCanvas(props: Props) {
  const ready = useWorkflowEditorStore(s => s.nodeDefinitions.length > 0)

  return (
    <div className="flex-1 min-h-0 min-w-0 relative">
      {ready
        ? <Flow {...props} />
        : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-7 h-7 border-2 border-border border-t-text-mute rounded-full animate-spin" />
          </div>
        )
      }
    </div>
  )
}
