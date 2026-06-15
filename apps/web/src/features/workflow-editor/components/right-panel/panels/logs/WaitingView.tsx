import { useEffect, useState } from 'react'
import { Loader2, Radio, Clock, Crosshair, Tag } from 'lucide-react'
import type { NodeInfo } from './types'

interface WaitingPayload {
  waitingFor: string
  targetId?: string | null
  ttlSeconds?: number | null
  startedAt?: string | null
}

interface Props {
  nodeInfo: NodeInfo
  payload: WaitingPayload
  onCancel?: () => void
}

/**
 * Right-pane view rendered while a listen slot is open. Replaces the empty
 * "Select a node to view its details" placeholder with a richer status panel
 * — what we're waiting for, which resource the slot is pinned to, and a
 * countdown to the TTL expiry.
 */
export function WaitingView({ nodeInfo, payload, onCancel }: Props) {
  const { waitingFor, targetId, ttlSeconds, startedAt } = payload

  const [remaining, setRemaining] = useState<number | null>(() =>
    computeRemaining(ttlSeconds, startedAt),
  )

  useEffect(() => {
    if (ttlSeconds == null || !startedAt) return
    const tick = () => setRemaining(computeRemaining(ttlSeconds, startedAt))
    tick()
    const id = window.setInterval(tick, 1000)
    return () => window.clearInterval(id)
  }, [ttlSeconds, startedAt])

  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <div className="flex shrink-0 items-center gap-2 border-b border-[var(--border-faint)] px-3 py-1.5">
        <Loader2 className="h-3.5 w-3.5 animate-spin text-[var(--accent,#3b82f6)]" />
        <span className="text-[12px] font-medium text-[var(--text)]">
          {nodeInfo.label}
        </span>
        <span className="text-[11px] text-[var(--text-faint)]">waiting</span>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-4 py-4">
        <div className="flex items-center gap-2">
          <Radio className="h-4 w-4 text-[var(--accent,#3b82f6)]" />
          <div className="flex flex-col">
            <span className="text-[13px] font-medium text-[var(--text)]">
              Listening for {waitingFor}
            </span>
            <span className="text-[11.5px] text-[var(--text-mute)]">
              Trigger this event from the source to fire the workflow once.
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-2 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] p-3">
          <DetailRow icon={<Tag className="h-3.5 w-3.5" />} label="Event">
            <span className="font-mono text-[11.5px] text-[var(--text)]">
              {waitingFor}
            </span>
          </DetailRow>
          {targetId && (
            <DetailRow icon={<Crosshair className="h-3.5 w-3.5" />} label="Target">
              <span className="font-mono text-[11.5px] text-[var(--text)]">
                {targetId}
              </span>
            </DetailRow>
          )}
          <DetailRow icon={<Clock className="h-3.5 w-3.5" />} label="Slot expires">
            <span className="font-mono text-[11.5px] text-[var(--text)]">
              {remaining == null
                ? '—'
                : remaining <= 0
                  ? 'expired'
                  : formatRemaining(remaining)}
            </span>
          </DetailRow>
        </div>

        <ol className="flex list-decimal flex-col gap-1 pl-5 text-[11.5px] text-[var(--text-mute)]">
          <li>Open the source app (Instagram / Facebook / WhatsApp).</li>
          <li>Perform the action that matches the event above.</li>
          <li>
            The first matching webhook fires this run; the slot then closes
            automatically.
          </li>
        </ol>

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="self-start rounded-[6px] border border-[var(--border-faint)] bg-[var(--surface)] px-3 py-1.5 text-[11.5px] text-[var(--text-mute)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
          >
            Cancel listen
          </button>
        )}
      </div>
    </div>
  )
}

function DetailRow({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="flex h-5 w-5 items-center justify-center text-[var(--text-faint)]">
        {icon}
      </span>
      <span className="w-[80px] text-[11px] uppercase tracking-wide text-[var(--text-faint)]">
        {label}
      </span>
      <span className="flex-1 truncate">{children}</span>
    </div>
  )
}

function computeRemaining(
  ttlSeconds: number | null | undefined,
  startedAt: string | null | undefined,
): number | null {
  if (ttlSeconds == null || !startedAt) return null
  const start = Date.parse(startedAt)
  if (Number.isNaN(start)) return null
  const elapsed = (Date.now() - start) / 1000
  return Math.max(0, Math.floor(ttlSeconds - elapsed))
}

function formatRemaining(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${String(s).padStart(2, '0')}s`
}
