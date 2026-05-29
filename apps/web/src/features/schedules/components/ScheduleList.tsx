import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { useToast, useConfirm, Empty } from '@/shared/components'
import { useToggleSchedule, useDeleteSchedule, useRunSchedule } from '../hooks/useSchedules'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { Schedule } from '../types/schedulesTypes'

interface Props { items: Schedule[] }

function fmtNextRun(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  const now = new Date()
  const diff = d.getTime() - now.getTime()
  const mins = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  if (mins < 1)   return 'in <1 min'
  if (mins < 60)  return `in ${mins}m`
  if (hours < 24) return `in ${hours}h`
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function statusDot(s: string) {
  if (s === 'error')  return 'err'
  if (s === 'paused') return 'warn'
  if (s === 'draft')  return 'draft'
  return 'ok'
}

export function ScheduleList({ items }: Props) {
  const navigate   = useNavigate()
  const { toast }  = useToast()
  const confirm    = useConfirm()
  const toggle     = useToggleSchedule()
  const remove     = useDeleteSchedule()
  const run        = useRunSchedule()

  const handleToggle = async (s: Schedule, e: React.MouseEvent) => {
    e.stopPropagation()
    await toggle.mutateAsync(s.id)
    toast(s.is_active ? 'Paused' : 'Resumed', { variant: 'ok', description: s.name })
  }

  const handleDelete = async (s: Schedule, e: React.MouseEvent) => {
    e.stopPropagation()
    const ok = await confirm({
      title: 'Delete schedule',
      message: `Delete "${s.name}"? The workflow will be removed.`,
      confirmText: 'Delete', variant: 'danger',
    })
    if (!ok) return
    await remove.mutateAsync(s.id)
    toast('Deleted', { variant: 'ok' })
  }

  const handleRun = async (s: Schedule, e: React.MouseEvent) => {
    e.stopPropagation()
    const res = await run.mutateAsync(s.id)
    toast('Triggered', { variant: 'ok', description: `Execution ${res.execution_id.slice(0, 8)}… started` })
  }

  if (items.length === 0) {
    return (
      <div className="panel">
        <Empty
          icon={<Icons.Clock />}
          title="No scheduled workflows"
          description="Add a cron trigger node to any workflow to schedule it."
          className="flex-1 justify-center"
        />
      </div>
    )
  }

  return (
    <div className="panel">
      <div className="table table-sched">
        <div className="table-head">
          <span></span>
          <span>Name</span>
          <span>Cron</span>
          <span>Next run</span>
          <span>Last run</span>
          <span>Status</span>
          <span></span>
        </div>
        {items.map(s => (
          <div
            key={s.id}
            className="table-row group cursor-pointer"
            onClick={() => navigate(APP_ROUTES.WORKFLOW(s.id))}
          >
            <span className={`status-dot ${statusDot(s.status)}`} />

            <span className="row-name">
              {s.name}
              {s.timezone && s.timezone !== 'UTC' && (
                <span className="ml-2 text-[10.5px] font-mono text-[var(--text-dim)]">{s.timezone}</span>
              )}
            </span>

            <span className="row-mono font-mono text-[11.5px]">
              {s.cron_expression || '—'}
            </span>

            <span className="row-mono flex items-center gap-1.5">
              <Icons.Clock style={{ width: 11, height: 11, color: 'var(--text-faint)' }} />
              {fmtNextRun(s.next_run)}
            </span>

            <span className="row-mono">
              {s.last_run
                ? <span className={s.last_run_status === 'failed' ? 'text-[var(--err)]' : ''}>{s.last_run}</span>
                : '—'
              }
            </span>

            <span className={`status-pill ${statusDot(s.status)}`}>{s.status}</span>

            {/* Row actions */}
            <span className="flex items-center justify-end gap-1" onClick={e => e.stopPropagation()}>
              <button
                onClick={e => handleRun(s, e)}
                disabled={run.isPending || s.status === 'draft'}
                className="w-[24px] h-[24px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[oklch(0.78_0.14_145/0.14)] hover:text-[var(--ok)] transition-all disabled:opacity-30"
                title="Run now"
              >
                <Icons.Activity style={{ width: 12, height: 12 }} />
              </button>

              <button
                onClick={e => handleToggle(s, e)}
                disabled={toggle.isPending}
                className="w-[24px] h-[24px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[var(--surface-2)] hover:text-[var(--text)] transition-all disabled:opacity-30"
                title={s.is_active ? 'Pause' : 'Resume'}
              >
                {s.is_active
                  ? <Icons.Pause style={{ width: 11, height: 11 }} />
                  : <Icons.Activity style={{ width: 11, height: 11 }} />
                }
              </button>

              <button
                onClick={e => handleDelete(s, e)}
                disabled={remove.isPending}
                className="w-[24px] h-[24px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[oklch(0.70_0.18_22/0.14)] hover:text-[var(--err)] transition-all"
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
