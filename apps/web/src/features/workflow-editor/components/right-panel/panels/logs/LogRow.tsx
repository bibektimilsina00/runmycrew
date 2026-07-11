import React from 'react'
import { cn } from '@/lib/cn'
import type { RunLog } from '@/features/runs/store/runsStore'
import { getIcon } from '../../../../utils/icon-map'
import type { NodeInfo } from './types'
import { logStatus } from './types'

interface Props {
  log: RunLog
  selected: boolean
  nodeInfo: NodeInfo
  onClick: () => void
}

function formatDuration(ms: unknown): string {
  if (typeof ms !== 'number' || !Number.isFinite(ms) || ms < 0) return ''
  if (ms < 1000) return `${Math.round(ms)}ms`
  const s = ms / 1000
  if (s < 60) return `${s.toFixed(s < 10 ? 2 : 1)}s`
  const m = Math.floor(s / 60)
  const rem = Math.round(s - m * 60)
  return `${m}m ${rem}s`
}

/**
 * Single row inside the Runs list. Shows the node's badge + label and the
 * execution duration (when known). Failure rows render the text in the
 * error color — no border, matching the rest of the inspector.
 */
export function LogRow({ log, selected, nodeInfo, onClick }: Props) {
  const status = logStatus(log)
  const duration = formatDuration(log.payload?.duration_ms)
  const isFailed = status === 'failed'

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex w-full items-center gap-2 rounded-[8px] px-2 py-1.5 text-left text-[12px] transition-colors',
        isFailed
          ? selected
            ? 'bg-[var(--surface-2)] text-[var(--err)]'
            : 'text-[var(--err)] hover:bg-[var(--surface)]'
          : selected
            ? 'bg-[var(--surface-2)] text-[var(--text)]'
            : 'text-[var(--text-mute)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
      )}
    >
      <div
        className={`flex size-[22px] shrink-0 items-center justify-center rounded-[5px] transition-shadow duration-200 ${
          nodeInfo.color === '#ffffff' ? 'bg-white border border-zinc-700/30 shadow-[0_1px_2px_rgba(0,0,0,0.2)]' : 'shadow-sm'
        }`}
        style={nodeInfo.color !== '#ffffff' ? { background: nodeInfo.color ?? 'var(--surface-3)' } : undefined}
      >
        {React.cloneElement(
          getIcon(nodeInfo.icon) as React.ReactElement<{ className?: string }>,
          { className: 'size-[13px] text-white' },
        )}
      </div>
      <span
        className={cn(
          'flex-1 truncate font-medium',
          isFailed ? 'text-[var(--err)]' : 'text-[var(--text)]',
        )}
        title={nodeInfo.label}
      >
        {nodeInfo.label}
      </span>
      {duration && (
        <span
          className={cn(
            'shrink-0 font-mono text-[10.5px]',
            isFailed ? 'text-[var(--err)] opacity-80' : 'text-[var(--text-faint)]',
          )}
        >
          {duration}
        </span>
      )}
    </button>
  )
}
