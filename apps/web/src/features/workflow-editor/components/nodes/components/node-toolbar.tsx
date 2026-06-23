import { useEffect, useRef, useState } from 'react'
import { Play, Square, Lock, LockOpen, ArrowLeftRight, ArrowUpDown, Copy, Trash2, Loader2 } from 'lucide-react'
import { useReactFlow } from 'reactflow'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'

interface NodeToolbarProps {
  id: string
  selected: boolean
}

// Chip base = neutral surface so the toolbar reads as quiet glyphs at
// rest. Accent (theme primary) only applies when the chip's underlying
// state is active — Run while running, Lock while locked — surfaced via
// the BTN_ACTIVE modifier below. Hover stays subtle (surface bump) so
// it never looks like an "active" state on idle chips.
const BTN =
  'flex size-[24px] items-center justify-center rounded-[7px] ' +
  'bg-[var(--surface)]/80 border border-[var(--border-faint)] text-[var(--text-mute)] ' +
  'backdrop-blur-sm transition-colors ' +
  'hover:bg-[var(--surface-2)] hover:border-[var(--border-soft)] hover:text-[var(--text)] ' +
  '[&_svg]:size-[12px] disabled:opacity-40 disabled:cursor-not-allowed'

// Applied to a chip whose underlying state is currently "on". Uses the
// accent token so the highlight retints with the active palette.
const BTN_ACTIVE =
  'bg-[var(--accent)] border-[color-mix(in_oklab,var(--accent)_70%,transparent)] text-white ' +
  'hover:bg-[var(--accent)] hover:text-white hover:brightness-110'

const NODE_HEIGHT_ESTIMATE = 30 // px above the node

export const NodeToolbar = ({ id, selected }: NodeToolbarProps) => {
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const removeNode = useWorkflowEditorStore(s => s.removeNode)
  const duplicateNode = useWorkflowEditorStore(s => s.duplicateNode)
  const toggleNodeLock = useWorkflowEditorStore(s => s.toggleNodeLock)
  const toggleNodeHandleDirection = useWorkflowEditorStore(s => s.toggleNodeHandleDirection)
  const runNode = useWorkflowEditorStore(s => s.runNode)
  const stopNode = useWorkflowEditorStore(s => s.stopNode)
  const runState = useWorkflowEditorStore(s => s.nodeRuns[id])
  const { getNode } = useReactFlow()

  const node = nodes.find(n => n.id === id)
  const isLocked = node?.data?.locked ?? false
  const isHorizontal = (node?.data?.handleDirection ?? 'horizontal') === 'horizontal'
  const isRunning = runState?.status === 'running'

  // Edge avoidance: flip toolbar below the node when too close to viewport top.
  const rootRef = useRef<HTMLDivElement>(null)
  const [placeBelow, setPlaceBelow] = useState(false)

  useEffect(() => {
    if (!selected) return
    const el = rootRef.current?.parentElement
    if (!el) return
    const rect = el.getBoundingClientRect()
    setPlaceBelow(rect.top < NODE_HEIGHT_ESTIMATE + 8)
  }, [selected, id, getNode])

  return (
    <div
      ref={rootRef}
      className={cn(
        // Right-aligned: anchor the toolbar to the node's right edge so
        // the action chips never overlap the node title at the left.
        'pointer-events-auto absolute right-0 flex items-center gap-[5px]',
        'transition-opacity duration-150',
        selected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100',
        placeBelow ? '-bottom-[30px]' : '-top-[30px]',
      )}
      onPointerDown={e => e.stopPropagation()}
      onClick={e => e.stopPropagation()}
    >
      {/* Run / Stop — single slot toggle. While running the chip lights
          up red (active danger state); idle keeps neutral but tints text
          on the last terminal status. */}
      {isRunning ? (
        <button
          type="button"
          className={cn(
            BTN,
            'bg-[var(--err)] border-[var(--err)] text-white hover:bg-[var(--err)] hover:text-white hover:brightness-110',
          )}
          title="Stop run"
          onClick={() => stopNode(id)}
        >
          <Square />
        </button>
      ) : (
        <button
          type="button"
          className={cn(
            BTN,
            runState?.status === 'success' && 'text-[var(--ok)] hover:text-[var(--ok)]',
            runState?.status === 'failed'  && 'text-[var(--err)] hover:text-[var(--err)]',
          )}
          title={runState?.status === 'failed' && runState.error
            ? `Run node — last error: ${runState.error}`
            : runState?.status === 'success' && runState.durationMs != null
              ? `Run node — last run ${runState.durationMs}ms`
              : 'Run node'}
          onClick={() => void runNode(id)}
          disabled={isLocked}
        >
          <Play />
        </button>
      )}

      {/* Show a small spinner-as-indicator only when running, separate from the
          toggle button so the layout doesn't shift mid-run. */}
      {isRunning && (
        <span className="flex size-[24px] items-center justify-center text-[var(--text-faint)]">
          <Loader2 className="size-[12px] animate-spin" />
        </span>
      )}

      <button
        type="button"
        className={cn(BTN, isLocked && BTN_ACTIVE)}
        title={isLocked ? 'Unlock node' : 'Lock node'}
        onClick={() => toggleNodeLock(id)}
        aria-pressed={isLocked}
      >
        {isLocked ? <Lock /> : <LockOpen />}
      </button>

      <button
        type="button"
        className={BTN}
        title={isHorizontal ? 'Switch to vertical handles' : 'Switch to horizontal handles'}
        onClick={() => toggleNodeHandleDirection(id)}
        aria-pressed={isHorizontal}
      >
        {isHorizontal ? <ArrowLeftRight /> : <ArrowUpDown />}
      </button>

      <button
        type="button"
        className={BTN}
        title="Duplicate node (⌘D)"
        onClick={() => duplicateNode(id)}
      >
        <Copy />
      </button>

      <button
        type="button"
        className={cn(
          BTN,
          // Delete is destructive — hover keeps the err tint but never
          // becomes the accent / "active" state since the action is a
          // momentary trigger, not a persistent toggle.
          'hover:bg-[var(--err)]/10 hover:border-[var(--err)]/30 hover:text-[var(--err)]',
        )}
        title="Delete node (⌫)"
        onClick={() => removeNode(id)}
      >
        <Trash2 />
      </button>
    </div>
  )
}
