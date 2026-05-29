import { useCallback, useMemo } from 'react'
import ReactFlow, {
  ReactFlowProvider,
  Background,
  BackgroundVariant,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useShallow } from 'zustand/react/shallow'
import { buildNodeTypes } from '../../constants/nodeTypes'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'

interface Props {
  nodes: Node[]
  edges: Edge[]
  onNodesChange: OnNodesChange
  onEdgesChange: OnEdgesChange
  onConnect?: OnConnect
}

function Flow({ nodes, edges, onNodesChange, onEdgesChange, onConnect }: Props) {
  const nodeDefinitions = useWorkflowEditorStore(useShallow(s => s.nodeDefinitions))

  // Computed once after definitions load — never changes reference after first mount.
  // useMemo dep array is stable because useShallow prevents re-renders when
  // array contents don't change. Flow is only mounted after definitions arrive
  // (see EditorCanvas guard below), so this runs exactly once.
  const nodeTypes = useMemo(() => buildNodeTypes(nodeDefinitions), [nodeDefinitions])

  const handleConnect: OnConnect = useCallback(
    (connection) => {
      if (onConnect) onConnect(connection)
    },
    [onConnect]
  )

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={handleConnect}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.1}
      maxZoom={2}
      defaultEdgeOptions={{ type: 'smoothstep', animated: false }}
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
          className="absolute inset-0 flex flex-col items-center justify-center gap-3 pointer-events-none"
          style={{ zIndex: 4 }}
        >
          <div className="w-[48px] h-[48px] rounded-[12px] bg-[var(--surface)] border border-[var(--border-faint)] flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-dim)" strokeWidth="1.5">
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
          </div>
          <div className="text-center">
            <p className="text-[13.5px] font-medium text-[var(--text-mute)]">Empty canvas</p>
            <p className="text-[12px] text-[var(--text-faint)] mt-0.5">
              Add nodes from the panel to build your workflow
            </p>
          </div>
        </div>
      )}
    </ReactFlow>
  )
}

export function EditorCanvas(props: Props) {
  const ready = useWorkflowEditorStore(s => s.nodeDefinitions.length > 0)

  return (
    <ReactFlowProvider>
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
    </ReactFlowProvider>
  )
}
