import { useCallback,  useMemo, useState } from 'react'
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
import { Search } from 'lucide-react'
import { buildNodeTypes } from '../../constants/nodeTypes'
import { CustomEdge } from '../edges/CustomEdge'
import { ContextMenu, type ContextMenuItem } from '../context-menu/ContextMenu'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../../stores/editorLayoutStore'
import { CanvasControls } from './CanvasControls'
import { CanvasFloatingButtons } from '../right-panel/CanvasFloatingButtons'
import { Modal } from '@/shared/components/Modal'
import { cn } from '@/lib/cn'

const edgeTypes = { custom: CustomEdge }

interface Props {
  nodes: Node[]
  edges: Edge[]
  onNodesChange: OnNodesChange
  onEdgesChange: OnEdgesChange
  onConnect?: OnConnect
  onSelectNode?: (nodeId: string) => void
  interactive?: boolean
  onToggleFullscreen?: () => void
  isFullscreen?: boolean
}

interface MenuState {
  type: 'node' | 'pane'
  x: number
  y: number
  nodeId?: string
}

function Flow({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onSelectNode,
  interactive = true,
  onToggleFullscreen,
  isFullscreen = false,
}: Props) {
  const nodeDefinitions = useWorkflowEditorStore(useShallow(s => s.nodeDefinitions))
  const focusTab = useEditorLayoutStore(s => s.focusTab)
  const setNodes = useWorkflowEditorStore(s => s.setNodes)
  const pushHistory = useWorkflowEditorStore(s => s.pushHistory)
  const { screenToFlowPosition, fitView, zoomIn, zoomOut } = useReactFlow()
  const [menu, setMenu] = useState<MenuState | null>(null)
  
  // ── Add Node Modal ────────────────────────────────────────────────────────
  const [addNodeOpen, setAddNodeOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)

  const filteredDefs = useMemo(() => {
    return nodeDefinitions.filter(def =>
      def.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      def.type.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [nodeDefinitions, searchQuery])

  const handleAddNode = useCallback((type: string) => {
    const def = nodeDefinitions.find(d => d.type === type)
    if (!def) return

    // Center of viewport
    const w = window.innerWidth
    const h = window.innerHeight
    const position = screenToFlowPosition({ x: w / 2, y: h / 2 })

    pushHistory()
    setNodes(ns => [...ns, {
      id: crypto.randomUUID(),
      type,
      position,
      data: { label: def.name, properties: {} },
    }])
    setAddNodeOpen(false)
    setSearchQuery('')
    setSelectedIndex(0)
  }, [nodeDefinitions, screenToFlowPosition, setNodes, pushHistory])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, filtered: typeof nodeDefinitions) => {
    if (filtered.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(prev => (prev + 1) % filtered.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(prev => (prev - 1 + filtered.length) % filtered.length)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      handleAddNode(filtered[selectedIndex].type)
    }
  }

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
      const node = nodes.find(n => n.id === id)
      const locked = (node?.data?.locked as boolean | undefined) ?? false
      const label = (node?.data?.label as string) || node?.type || 'this node'
      const fixWithCopilot = () => {
        s.setSelectedNodeId(id)
        useEditorLayoutStore.getState().focusTab('copilot')
        // Defer so the Copilot panel mounts + registers its listener first.
        setTimeout(
          () =>
            window.dispatchEvent(
              new CustomEvent('copilot-send-message', {
                detail: { message: `Fix the "${label}" node.` },
              }),
            ),
          80,
        )
      }
      return [
        { label: 'Copy', shortcut: '⌘C', onClick: () => { s.setNodes(ns => ns.map(n => ({ ...n, selected: n.id === id }))); s.copySelection() } },
        { label: 'Duplicate', shortcut: '⌘D', onClick: () => s.duplicateNode(id) },
        { label: locked ? 'Unlock' : 'Lock', onClick: () => s.toggleNodeLock(id) },
        { label: 'Fix with Copilot', dividerBefore: true, onClick: fixWithCopilot },
        { label: 'Delete', shortcut: '⌫', variant: 'danger', dividerBefore: true, onClick: () => s.removeNode(id) },
      ]
    }
    return [
      { label: 'Paste', shortcut: '⌘V', disabled: !s.clipboard, onClick: () => s.paste() },
      { label: 'Select all', shortcut: '⌘A', onClick: () => s.selectAll() },
      { label: 'Add node', dividerBefore: true, onClick: () => setAddNodeOpen(true) },
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
        onNodeContextMenu={interactive ? onNodeContextMenu : undefined}
        onPaneContextMenu={interactive ? onPaneContextMenu : undefined}
        onNodeDragStart={onNodeDragStart}
        nodesDraggable={interactive}
        nodesConnectable={interactive}
        elementsSelectable={interactive}
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
              onClick={() => focusTab('library')}
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

      <CanvasControls
        onFitView={() => fitView({ duration: 300, padding: 0.2 })}
        onZoomIn={() => zoomIn({ duration: 300 })}
        onZoomOut={() => zoomOut({ duration: 300 })}
        onCleanLayout={() => fitView({ duration: 400, padding: 0.2 })}
      />

      {menu && (
        <ContextMenu x={menu.x} y={menu.y} items={buildMenuItems()} onClose={() => setMenu(null)} />
      )}

      {/* Floating Action Buttons overlaid on top-right */}
      <CanvasFloatingButtons
        onToggleZenMode={onToggleFullscreen}
        zenMode={isFullscreen}
        onAddNodeClick={() => setAddNodeOpen(prev => !prev)}
        isAddNodeOpen={addNodeOpen}
      />

      {/* Centered Add Node Fuzzy Search command palette / popup modal */}
      <Modal
        open={addNodeOpen}
        onClose={() => {
          setAddNodeOpen(false)
          setSearchQuery('')
        }}
        title="Add Node"
        width="460px"
      >
        <div className="flex flex-col">
          <div className="relative mb-4 flex items-center">
            <Search className="absolute left-3.5 text-[var(--text-mute)] h-4 w-4 pointer-events-none" />
            <input
              type="text"
              placeholder="Search node types..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setSelectedIndex(0)
              }}
              onKeyDown={(e) => handleKeyDown(e, filteredDefs)}
              className="w-full bg-[var(--bg)] text-[var(--text)] text-[13.5px] pl-10 pr-4 py-2.5 rounded-[8px] border border-[var(--border-faint)] focus:outline-none focus:border-[var(--accent)]"
              autoFocus
            />
          </div>

          <div className="max-h-[320px] overflow-y-auto pr-1 flex flex-col gap-1 [scrollbar-width:thin] [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-thumb]:bg-[var(--border-faint)] [&::-webkit-scrollbar-thumb]:rounded-full">
            {filteredDefs.map((def, idx) => {
              const isSelected = idx === selectedIndex
              return (
                <button
                  key={def.type}
                  onClick={() => handleAddNode(def.type)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={cn(
                    "w-full text-left px-3.5 py-3 rounded-[8px] flex items-center justify-between transition-colors border cursor-pointer",
                    isSelected
                      ? "bg-[var(--surface-hover)] border-[var(--border-soft)] text-[var(--text)]"
                      : "border-transparent text-[var(--text-mute)] hover:text-[var(--text)]"
                  )}
                >
                  <div className="flex-1 min-w-0 pr-4">
                    <p className="text-[13.5px] font-semibold truncate">{def.name}</p>
                    {def.description && (
                      <p className="text-[11.5px] text-[var(--text-faint)] mt-0.5 line-clamp-1 break-all">
                        {def.description}
                      </p>
                    )}
                  </div>
                  {def.category && (
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-[4px] bg-[var(--surface)] text-[var(--text-faint)] shrink-0">
                      {def.category}
                    </span>
                  )}
                </button>
              )
            })}
            {filteredDefs.length === 0 && (
              <p className="text-[12.5px] text-[var(--text-faint)] text-center py-8">No matching nodes found.</p>
            )}
          </div>
        </div>
      </Modal>
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
