import { Play, Square, Lock, LockOpen, ArrowLeftRight, ArrowUpDown, Trash2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'

interface NodeToolbarProps {
  id: string
}

const BTN =
  'flex size-[24px] items-center justify-center rounded-[7px] ' +
  'bg-[var(--surface)] border border-[var(--border-faint)] text-text-mute ' +
  'transition-colors hover:bg-[var(--surface-3)] hover:border-[var(--border-soft)] hover:text-text ' +
  '[&_svg]:size-[12px]'

export const NodeToolbar = ({ id }: NodeToolbarProps) => {
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const removeNode = useWorkflowEditorStore(s => s.removeNode)
  const toggleNodeLock = useWorkflowEditorStore(s => s.toggleNodeLock)
  const toggleNodeHandleDirection = useWorkflowEditorStore(s => s.toggleNodeHandleDirection)

  const node = nodes.find(n => n.id === id)
  const isLocked = node?.data?.locked ?? false
  const isHorizontal = (node?.data?.handleDirection ?? 'horizontal') === 'horizontal'

  return (
    <div
      className="
        pointer-events-auto absolute -top-[36px] left-1/2 -translate-x-1/2
        flex items-center gap-[5px]
        opacity-0 transition-opacity duration-150 group-hover:opacity-100
      "
    >
      <button type="button" className={BTN} title="Run node">
        <Play />
      </button>

      <button type="button" className={BTN} title="Stop node">
        <Square />
      </button>

      <button
        type="button"
        className={cn(BTN, isLocked && 'text-ok hover:text-ok')}
        title={isLocked ? 'Unlock node' : 'Lock node'}
        onClick={() => toggleNodeLock(id)}
      >
        {isLocked ? <LockOpen /> : <Lock />}
      </button>

      <button
        type="button"
        className={BTN}
        title={isHorizontal ? 'Vertical handles' : 'Horizontal handles'}
        onClick={() => toggleNodeHandleDirection(id)}
      >
        {isHorizontal ? <ArrowUpDown /> : <ArrowLeftRight />}
      </button>

      <button
        type="button"
        className={cn(BTN, 'hover:bg-err/10 hover:border-err/30 hover:text-err')}
        title="Delete node"
        onClick={() => removeNode(id)}
      >
        <Trash2 />
      </button>
    </div>
  )
}
