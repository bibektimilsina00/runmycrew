import { useState } from 'react'
import { AlertOctagon, AlertTriangle, ChevronDown, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { StructuredError } from './structuredError'

interface Props {
  data: StructuredError
}

/**
 * Inspector card for structured error payloads.
 *
 * Layout: severity icon + title (bold) → summary paragraph → bulleted
 * action list → collapsible "Raw response" block. The raw body opens
 * shut by default so the user sees the human-readable info first and
 * power users can still drill in.
 *
 * The card is presentation-only — purely driven by `data`. No backend
 * coupling beyond the structured-error contract.
 */
export function StructuredErrorCard({ data }: Props) {
  const [showRaw, setShowRaw] = useState(false)
  const isWarning = data.severity === 'warning'
  const Icon = isWarning ? AlertTriangle : AlertOctagon
  const accent = isWarning
    ? { tint: 'rgba(234,179,8,0.06)', color: 'var(--warn,#eab308)' }
    : { tint: 'rgba(239,68,68,0.06)', color: 'var(--err,#ef4444)' }

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-3 py-3">
      <div
        className={cn(
          'flex items-start gap-2.5 rounded-[8px] border border-[var(--border-faint)] p-3',
        )}
        style={{ background: accent.tint }}
      >
        <Icon
          className="mt-[1px] h-4 w-4 shrink-0"
          style={{ color: accent.color }}
        />
        <div className="min-w-0 flex-1">
          <div className="text-[13px] font-semibold leading-snug text-[var(--text)]">
            {data.title}
          </div>
          {data.summary && (
            <p className="mt-1.5 text-[12px] leading-relaxed text-[var(--text-mute)]">
              {data.summary}
            </p>
          )}
        </div>
      </div>

      {data.actions.length > 0 && (
        <div className="mt-3 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] p-3">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-mute)]">
            What to do
          </div>
          <ul className="mt-2 flex flex-col gap-1.5">
            {data.actions.map((action, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-[12px] leading-snug text-[var(--text)]"
              >
                <CheckCircle2
                  className="mt-[2px] h-3.5 w-3.5 shrink-0 text-[var(--text-faint)]"
                  aria-hidden
                />
                <span className="min-w-0 flex-1">{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.raw && (
        <div className="mt-3 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)]">
          <button
            type="button"
            onClick={() => setShowRaw((v) => !v)}
            className={cn(
              'flex w-full items-center gap-1.5 rounded-t-[8px] px-3 py-2 text-left',
              'text-[11px] font-medium uppercase tracking-wide text-[var(--text-mute)]',
              'transition-colors hover:bg-[var(--surface-2)]',
              !showRaw && 'rounded-b-[8px]',
            )}
          >
            <ChevronDown
              className={cn(
                'h-3 w-3 shrink-0 transition-transform',
                !showRaw && '-rotate-90',
              )}
            />
            Raw response from upstream
          </button>
          {showRaw && (
            <pre
              className={cn(
                'max-h-[280px] overflow-auto whitespace-pre-wrap break-all border-t border-[var(--border-faint)]',
                'px-3 py-2 text-[11px] leading-relaxed text-[var(--text-mute)]',
              )}
            >
              {data.raw}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
