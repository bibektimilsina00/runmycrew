import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { useToast, useConfirm, Empty } from '@/shared/components'
import { useToggleLoop, useDeleteLoop, useDuplicateLoop, useRunLoop } from '../hooks/useLoops'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { Loop } from '../types/loopsTypes'

interface Props {
  items: Loop[]
}

function statusDot(s: string) {
  if (s === 'error')  return 'err'
  if (s === 'paused') return 'warn'
  if (s === 'draft')  return 'draft'
  return 'ok'
}

function statusPill(s: string) {
  if (s === 'error')  return 'err'
  if (s === 'paused') return 'warn'
  if (s === 'draft')  return 'draft'
  return 'ok'
}

export function LoopList({ items }: Props) {
  const navigate  = useNavigate()
  const { toast } = useToast()
  const confirm   = useConfirm()
  const toggle    = useToggleLoop()
  const remove    = useDeleteLoop()
  const duplicate = useDuplicateLoop()
  const run       = useRunLoop()

  const handleToggle = async (a: Loop, e: React.MouseEvent) => {
    e.stopPropagation()
    await toggle.mutateAsync(a.id)
    toast(a.is_active ? 'Paused' : 'Resumed', { variant: 'ok', description: a.name })
  }

  const handleDelete = async (a: Loop, e: React.MouseEvent) => {
    e.stopPropagation()
    const ok = await confirm({ title: 'Delete loop', message: `Delete "${a.name}"? This cannot be undone.`, confirmText: 'Delete', variant: 'danger' })
    if (!ok) return
    await remove.mutateAsync(a.id)
    toast('Deleted', { variant: 'ok', description: a.name })
  }

  const handleDuplicate = async (a: Loop, e: React.MouseEvent) => {
    e.stopPropagation()
    await duplicate.mutateAsync(a.id)
    toast('Duplicated', { variant: 'ok', description: `"${a.name} (copy)" created` })
  }

  const handleRun = async (a: Loop, e: React.MouseEvent) => {
    e.stopPropagation()
    const result = await run.mutateAsync(a.id)
    toast('Triggered', { variant: 'ok', description: `Execution ${result.execution_id.slice(0, 8)}… started` })
  }

  if (items.length === 0) {
    return (
      <div className="panel">
        <Empty
          icon={<Icons.Bolt />}
          title="No loops"
          description="No loops match your current filter."
          className="flex-1 justify-center"
        />
      </div>
    )
  }

  return (
    <div className="panel">
      <div className="table">
        <div className="table-head">
          <span></span>
          <span>Name</span>
          <span>Kind</span>
          <span>Runs</span>
          <span>Last run</span>
          <span>Status</span>
          <span></span>
        </div>
        {items.map(a => (
          <div
            key={a.id}
            className="table-row group cursor-pointer"
            onClick={() => navigate(APP_ROUTES.CREW_EDITOR(a.id))}
          >
            <span className={`status-dot ${statusDot(a.status)}`} />

            <span className="row-name">{a.name}</span>

            <span className="row-kind">
              {a.kind === 'agent'    ? <Icons.Spark  style={{ width: 13, height: 13 }} /> :
               a.kind === 'schedule' ? <Icons.Clock  style={{ width: 13, height: 13 }} /> :
                                       <Icons.Flow   style={{ width: 13, height: 13 }} />}
              {a.kind}
            </span>

            <span className="row-mono">{a.execution_count.toLocaleString()}</span>

            <span className="row-mono">{a.last_run ?? '—'}</span>

            <span className={`status-pill ${statusPill(a.status)}`}>{a.status}</span>

            {/* Actions — visible on hover */}
            <span className="flex items-center justify-end gap-1" onClick={e => e.stopPropagation()}>
              {/* Run */}
              <button
                onClick={e => handleRun(a, e)}
                disabled={run.isPending || a.status === 'draft'}
                className="w-[24px] h-[24px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[oklch(0.78_0.14_145/0.14)] hover:text-[var(--ok)] transition-all disabled:opacity-30"
                title="Run now"
              >
                <Icons.Activity style={{ width: 12, height: 12 }} />
              </button>

              {/* Pause / Resume */}
              <button
                onClick={e => handleToggle(a, e)}
                disabled={toggle.isPending || a.status === 'draft'}
                className="w-[24px] h-[24px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[var(--surface-2)] hover:text-[var(--text)] transition-all disabled:opacity-30"
                title={a.is_active ? 'Pause' : 'Resume'}
              >
                {a.is_active
                  ? <Icons.Pause style={{ width: 11, height: 11 }} />
                  : <Icons.Activity style={{ width: 11, height: 11 }} />
                }
              </button>

              {/* Duplicate */}
              <button
                onClick={e => handleDuplicate(a, e)}
                disabled={duplicate.isPending}
                className="w-[24px] h-[24px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[var(--surface-2)] hover:text-[var(--text)] transition-all disabled:opacity-30"
                title="Duplicate"
              >
                <Icons.Copy style={{ width: 11, height: 11 }} />
              </button>

              {/* Delete */}
              <button
                onClick={e => handleDelete(a, e)}
                disabled={remove.isPending}
                className="w-[24px] h-[24px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[oklch(0.70_0.18_22/0.14)] hover:text-[var(--err)] transition-all disabled:opacity-30"
                title="Delete"
              >
                <Icons.Trash style={{ width: 11, height: 11 }} />
              </button>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
