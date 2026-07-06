import type { ReactNode } from 'react'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'

/**
 * Loop-engineering chrome for the `ai.agent_crew` orchestrator node. Renders
 * ONLY for that node type (guarded by the caller). Three blocks:
 *   1. A clickable 5-level verification ladder that writes `verificationLevel`
 *      back through the same property-change handler every field uses.
 *   2. A static legend of the five named terminal states.
 *   3. A best-effort run readout of the node's last manual run.
 *
 * Nothing here changes behaviour for any other node.
 */

interface CrewInspectorSectionProps {
  nodeId: string
  /** Current `verificationLevel` property value (1–5). */
  verificationLevel: number
  /** Writes the new `verificationLevel` via the inspector's property-change
   *  handler — persists + realtime-syncs like any other field. */
  onVerificationLevelChange: (level: number) => void
}

type Zone = 'autonomous' | 'objective' | 'assisted'

const RUNGS: { level: number; name: string; detail: string; zone: Zone }[] = [
  { level: 1, name: 'Deterministic', detail: 'assert · exit code', zone: 'autonomous' },
  { level: 2, name: 'Rule', detail: 'linter · schema', zone: 'autonomous' },
  { level: 3, name: 'Delayed field truth', detail: 'tests · deploy', zone: 'objective' },
  { level: 4, name: 'Model-as-judge', detail: 'rubric', zone: 'assisted' },
  { level: 5, name: 'Human checkpoint', detail: '', zone: 'assisted' },
]

const ZONE_COLOR: Record<Zone, string> = {
  autonomous: 'var(--good)',
  objective: 'var(--accent)',
  assisted: 'var(--warn)',
}

const ZONE_LABEL: Record<Zone, string> = {
  autonomous: 'Autonomous',
  objective: 'Objective',
  assisted: 'Assisted',
}

interface TerminalState {
  key: string
  color: string
  meaning: string
}

const TERMINAL_STATES: TerminalState[] = [
  { key: 'success', color: 'var(--good)', meaning: 'Verified change accepted.' },
  { key: 'no_op', color: 'var(--text-faint)', meaning: 'Nothing needed changing.' },
  { key: 'blocked', color: 'var(--warn)', meaning: 'Cannot proceed without input.' },
  { key: 'stalled', color: 'var(--warn)', meaning: 'No progress across rounds.' },
  { key: 'exhausted', color: 'var(--err)', meaning: 'Ran out of rounds or budget.' },
]

/** Maps a run's `terminal_state`/`status` to a legend color. */
function terminalColor(state: string | undefined): string {
  const match = TERMINAL_STATES.find(t => t.key === state)
  if (match) return match.color
  if (state === 'failed' || state === 'error') return 'var(--err)'
  return 'var(--text-faint)'
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <span className="font-mono text-[9.5px] font-semibold uppercase tracking-[0.09em] text-[var(--text-faint)]">
      {children}
    </span>
  )
}

export function CrewInspectorSection({
  nodeId,
  verificationLevel,
  onVerificationLevelChange,
}: CrewInspectorSectionProps) {
  // Best-effort last-run readout. `nodeRuns` is the same store slice the
  // Inputs section reads; `output` is the node's raw `output_data`.
  const run = useWorkflowEditorStore(s => s.nodeRuns[nodeId])
  const output = (run?.output ?? null) as Record<string, unknown> | null
  const hasReadout = !!output && (run?.status === 'success' || run?.status === 'failed')

  const activeLevel =
    Number.isFinite(verificationLevel) && verificationLevel >= 1 && verificationLevel <= 5
      ? Math.round(verificationLevel)
      : 1

  return (
    <div className="flex flex-col gap-5 border-t border-[var(--border-faint)] px-4 pb-6 pt-4">
      {/* ── 1. Verification ladder ─────────────────────────────────────── */}
      <div className="flex flex-col gap-2.5">
        <SectionLabel>Verification ladder</SectionLabel>
        <div className="flex flex-col gap-1">
          {RUNGS.map(rung => {
            const active = rung.level === activeLevel
            const color = ZONE_COLOR[rung.zone]
            return (
              <button
                key={rung.level}
                type="button"
                onClick={() => onVerificationLevelChange(rung.level)}
                aria-pressed={active}
                className={cn(
                  'group flex items-center gap-2.5 rounded-[8px] border px-2.5 py-1.5 text-left transition-colors',
                  active
                    ? 'border-transparent bg-[var(--surface-2)]'
                    : 'border-transparent hover:bg-[var(--surface)]',
                )}
                style={active ? { borderColor: color, background: `color-mix(in srgb, ${color} 12%, transparent)` } : undefined}
              >
                <span
                  className="flex size-[20px] shrink-0 items-center justify-center rounded-[5px] font-mono text-[10px] font-bold"
                  style={{
                    color: active ? '#fff' : color,
                    background: active ? color : `color-mix(in srgb, ${color} 16%, transparent)`,
                  }}
                >
                  L{rung.level}
                </span>
                <span className="min-w-0 flex-1">
                  <span
                    className={cn(
                      'block truncate text-[12px] font-medium',
                      active ? 'text-[var(--text)]' : 'text-[var(--text-mute)] group-hover:text-[var(--text)]',
                    )}
                  >
                    {rung.name}
                    {rung.detail && (
                      <span className="ml-1 font-normal text-[var(--text-faint)]"> ({rung.detail})</span>
                    )}
                  </span>
                </span>
                <span
                  className="shrink-0 font-mono text-[9px] uppercase tracking-[0.06em]"
                  style={{ color }}
                >
                  {ZONE_LABEL[rung.zone]}
                </span>
              </button>
            )
          })}
        </div>
        <p className="text-[10.5px] leading-snug text-[var(--text-faint)]">
          A crew is only as autonomous as the level its checker truly sits at — don&apos;t report L4 as L1.
        </p>
      </div>

      {/* ── 2. Terminal states legend ──────────────────────────────────── */}
      <div className="flex flex-col gap-2.5">
        <SectionLabel>Terminal states</SectionLabel>
        <div className="flex flex-col gap-1.5">
          {TERMINAL_STATES.map(t => (
            <div key={t.key} className="flex items-center gap-2 text-[11.5px]">
              <span
                className="size-[8px] shrink-0 rounded-full"
                style={{ background: t.color }}
              />
              <span className="w-[74px] shrink-0 font-mono text-[10.5px] font-medium text-[var(--text)]">
                {t.key}
              </span>
              <span className="min-w-0 flex-1 truncate text-[var(--text-mute)]">{t.meaning}</span>
            </div>
          ))}
        </div>
        <p className="text-[10.5px] leading-snug text-[var(--text-faint)]">
          An error or exhausted budget never counts as success.
        </p>
      </div>

      {/* ── 3. Run readout (best-effort) ───────────────────────────────── */}
      {hasReadout && output && (
        <RunReadout output={output} runStatus={run?.status} />
      )}
    </div>
  )
}

function RunReadout({
  output,
  runStatus,
}: {
  output: Record<string, unknown>
  runStatus: string | undefined
}) {
  const terminalState =
    (output.terminal_state as string | undefined) ??
    (output.status as string | undefined) ??
    runStatus
  const rounds = output.rounds as number | undefined
  const usage = (output.usage ?? null) as Record<string, unknown> | null
  const costUsd = (usage?.cost_usd ?? output.cost_usd) as number | undefined
  const costPerChange = output.cost_per_accepted_change as number | null | undefined

  const color = terminalColor(terminalState)

  return (
    <div className="flex flex-col gap-2.5">
      <SectionLabel>Last run</SectionLabel>
      <div className="flex flex-col gap-2 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] p-3">
        <div className="flex items-center gap-2">
          <span
            className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10.5px] font-semibold"
            style={{ color, background: `color-mix(in srgb, ${color} 15%, transparent)` }}
          >
            <span className="size-[6px] rounded-full" style={{ background: color }} />
            {terminalState ?? 'unknown'}
          </span>
          {typeof rounds === 'number' && (
            <span className="font-mono text-[10.5px] text-[var(--text-mute)]">
              {rounds} {rounds === 1 ? 'round' : 'rounds'}
            </span>
          )}
        </div>
        <div className="flex items-center justify-between gap-3 text-[11px]">
          <span className="text-[var(--text-faint)]">Cost</span>
          <span className="font-mono text-[var(--text)]">
            {typeof costUsd === 'number' ? `$${costUsd.toFixed(3)}` : '—'}
          </span>
        </div>
        <div className="flex items-center justify-between gap-3 text-[11px]">
          <span className="text-[var(--text-faint)]">Cost / accepted change</span>
          <span className="font-mono text-[var(--text)]">
            {typeof costPerChange === 'number' ? `$${costPerChange.toFixed(3)} / change` : '—'}
          </span>
        </div>
      </div>
    </div>
  )
}
