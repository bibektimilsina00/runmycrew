import { useEffect, useRef, useState } from 'react'
import { Play, Square, Lock, LockOpen, ArrowLeftRight, ArrowUpDown, Copy, Trash2, Loader2 } from 'lucide-react'
import { useReactFlow } from 'reactflow'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'

interface NodeToolbarProps {
  id: string
  selected: boolean
}

// Chip base = solid surface-2 fill + soft border + muted glyph so the
// chip reads as a real tappable surface at rest. Pointer hover paints
// the accent (theme primary) so the action being pointed at lights up.
// Solid bg avoids the alpha-on-CSS-var pitfall where Tailwind's /N
// opacity modifier silently drops; this guarantees a visible fill.
const BTN =
  'flex size-[24px] items-center justify-center rounded-[7px] ' +
  'bg-[var(--surface-2)] border border-[var(--border-soft)] text-[var(--text-mute)] ' +
  'transition-colors ' +
  'hover:bg-[var(--accent)] hover:border-[color-mix(in_oklab,var(--accent)_70%,transparent)] hover:text-white ' +
  '[&_svg]:size-[12px] disabled:opacity-40 disabled:cursor-not-allowed'

// Applied to a chip whose underlying state is currently "on" (Lock when
// locked). Persistent accent fill so the user can read the toggle state
// even when not hovering.
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
        // Right-aligned with a small inset so the chips never sit flush
        // against the node's right edge — reads as intentional padding
        // instead of touching the border.
        'pointer-events-auto absolute right-2 flex items-center gap-[5px]',
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
          // Delete shares the idle surface-2 fill with the rest of the
          // toolbar, then flips to a solid err on hover instead of accent
          // so the destructive intent reads at a glance. Avoiding the
          // /N alpha modifier here too — Tailwind silently drops alpha
          // on CSS-var values, which would have left the chip
          // colour-shift-less on hover.
          'hover:bg-[var(--err)] hover:border-[var(--err)] hover:text-white',
        )}
        title="Delete node (⌫)"
        onClick={() => removeNode(id)}
      >
        <Trash2 />
      </button>
    </div>
  )
}
