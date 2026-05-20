import React, { useState } from 'react'
import { Handle, Position } from 'reactflow'
import { Repeat2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useExecutionStore } from '@/stores/execution-store'
import { useWorkflowStore } from '@/stores/workflow-store'
import { NodeToolbar } from './components/node-toolbar'
import { LOOP_START_HANDLE_ID, LOOP_END_HANDLE_ID, LOOP_DIMS } from '../utils/loop-utils'

const LOOP_TYPE_LABEL: Record<string, string> = {
  for_each: 'For Each',
  for: 'For',
  while: 'While',
  do_while: 'Do While',
}

interface LoopNodeProps {
  id: string
  data: any
  type: string
  selected: boolean
}

export const LoopNode: React.FC<LoopNodeProps> = ({ id, data, selected }) => {
  const nodeStatuses = useExecutionStore(s => s.nodeStatuses)
  const { updateNodeData } = useWorkflowStore()
  const allStatuses = Object.values(nodeStatuses)
  const status = allStatuses.map(s => s[id]).find(Boolean)

  const [isEditingLabel, setIsEditingLabel] = useState(false)
  const [editValue, setEditValue] = useState('')

  const label = data?.label || 'Loop'
  const loopType = data?.properties?.loop_type || 'for_each'
  const loopTypeLabel = LOOP_TYPE_LABEL[loopType] || loopType

  const isRunning = status === 'running'
  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'

  const width = data?.width ?? LOOP_DIMS.DEFAULT_WIDTH
  const height = data?.height ?? LOOP_DIMS.DEFAULT_HEIGHT

  const startEditLabel = () => { setEditValue(label); setIsEditingLabel(true) }
  const saveLabel = () => { updateNodeData(id, { label: editValue.trim() || 'Loop' }); setIsEditingLabel(false) }

  return (
    <div
      className={cn('group relative', isRunning && 'node-running-wrapper')}
      style={{ width, height }}
    >
      <div
        className={cn(
          'relative w-full h-full rounded-xl border transition-all bg-transparent',
          selected ? 'border-[#555]' : 'border-border',
          isCompleted && 'node-status-completed',
          isFailed && 'node-status-failed',
        )}
      >
        <NodeToolbar id={id} />

        {/* Input handle */}
        <Handle
          type="target"
          position={Position.Left}
          className="!bg-[var(--workflow-edge,#555)] !w-[7px] !h-5 !left-[-8px] !border-none !rounded-l-[2px] !rounded-r-none hover:!w-[10px] hover:!left-[-11px] hover:!rounded-l-full"
          style={{ top: LOOP_DIMS.HEADER_HEIGHT / 2 }}
        />

        {/* Header */}
        <div
          className="workflow-drag-handle flex items-center gap-2 px-3 border-b border-border select-none"
          style={{ height: LOOP_DIMS.HEADER_HEIGHT }}
          onDoubleClick={startEditLabel}
        >
          <div className="flex size-[24px] flex-shrink-0 items-center justify-center rounded-md bg-[#3b82f6]">
            <Repeat2 size={13} className="text-white" strokeWidth={2.5} />
          </div>
          {isEditingLabel ? (
            <input
              autoFocus
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              onBlur={saveLabel}
              onKeyDown={e => e.key === 'Enter' && saveLabel()}
              className="flex-1 bg-transparent border-none outline-none text-[13px] font-bold text-white"
            />
          ) : (
            <span className="flex-1 truncate font-bold text-[13px] text-white">{label}</span>
          )}
          <span className="text-[10px] font-medium text-[var(--text-muted)] bg-[var(--surface-3)] border border-border px-1.5 py-0.5 rounded flex-shrink-0">
            {loopTypeLabel}
          </span>
        </div>

        {/* Body */}
        <div
          className="relative workflow-drag-handle overflow-hidden"
          style={{ height: `calc(100% - ${LOOP_DIMS.HEADER_HEIGHT}px)` }}
          data-dragarea="true"
        >
          {/* Start pill — Sim: absolute top-[4px] left-[16px] */}
          <div className="absolute" style={{ top: 4, left: 16, zIndex: 10 }}>
            <div className="flex items-center h-[28px] px-3 rounded-lg bg-[var(--surface-3)] border border-border">
              <span className="text-[12px] font-semibold text-white select-none">Start</span>
            </div>
            {/* Handle sits at the right edge of the pill — ReactFlow measures its DOM position */}
            <Handle
              type="source"
              position={Position.Right}
              id={LOOP_START_HANDLE_ID}
              className="!bg-[var(--workflow-edge,#555)] !w-[7px] !h-5 !border-none !rounded-r-[2px] !rounded-l-none hover:!w-[10px] hover:!rounded-r-full"
              style={{ top: '50%', right: -8, transform: 'translateY(-50%)' }}
            />
          </div>

          {/* Drop hint */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <p className="text-[10px] text-[var(--text-muted)] opacity-20 select-none">
              Drop nodes here
            </p>
          </div>
        </div>

        {/* Loop output handle */}
        <Handle
          type="source"
          position={Position.Right}
          id={LOOP_END_HANDLE_ID}
          className="!bg-[var(--workflow-edge,#555)] !w-[7px] !h-5 !right-[-8px] !border-none !rounded-r-[2px] !rounded-l-none hover:!w-[10px] hover:!right-[-11px] hover:!rounded-r-full"
          style={{ top: LOOP_DIMS.HEADER_HEIGHT / 2 }}
        />
      </div>
    </div>
  )
}
