import { Play, Square, Lock, Copy, ArrowLeftRight, ArrowUpDown, Trash2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import { Button } from '@/shared/components'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'

interface NodeToolbarProps {
  id: string
}

export const NodeToolbar = ({ id }: NodeToolbarProps) => {
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const removeNode = useWorkflowEditorStore(s => s.removeNode)
  const toggleNodeLock = useWorkflowEditorStore(s => s.toggleNodeLock)
  const duplicateNode = useWorkflowEditorStore(s => s.duplicateNode)
  const toggleNodeHandleDirection = useWorkflowEditorStore(s => s.toggleNodeHandleDirection)

  const node = nodes.find(n => n.id === id)
  const isLocked = node?.data?.locked ?? false
  const isHorizontal = (node?.data?.handleDirection ?? 'horizontal') === 'horizontal'

  return (
    <div className="
      pointer-events-auto absolute -top-[42px] right-0
      flex items-center gap-1 p-1
      rounded-[8px] border border-border bg-bg2
      opacity-0 transition-opacity duration-150 group-hover:opacity-100
    ">
      <Button variant="icon-sm" title="Run node"><Play /></Button>
      <Button variant="icon-sm" title="Stop node"><Square /></Button>

      <Button
        variant="icon-sm"
        title={isLocked ? 'Unlock node' : 'Lock node'}
        onClick={() => toggleNodeLock(id)}
        className={cn(isLocked && 'bg-ok/10 text-ok border-ok/30 hover:bg-ok/20')}
      >
        <Lock />
      </Button>

      <Button
        variant="icon-sm"
        title="Duplicate node"
        onClick={() => duplicateNode(id)}
      >
        <Copy />
      </Button>

      <Button
        variant="icon-sm"
        title={isHorizontal ? 'Vertical handles' : 'Horizontal handles'}
        onClick={() => toggleNodeHandleDirection(id)}
      >
        {isHorizontal ? <ArrowUpDown /> : <ArrowLeftRight />}
      </Button>

      <Button
        variant="icon-sm"
        title="Delete node"
        className="text-err hover:bg-err/10 hover:border-err/30"
        onClick={() => removeNode(id)}
      >
        <Trash2 />
      </Button>
    </div>
  )
}
