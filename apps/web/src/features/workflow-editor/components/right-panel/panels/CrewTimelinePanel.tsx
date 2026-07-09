import { useMemo } from 'react'
import { Coins, Hash, Users } from 'lucide-react'
import type { Run } from '@/features/runs/store/runsStore'

type NodeMetaMap = Map<string, { label: string; color?: string }>

interface CrewTimelinePanelProps {
  runs: Run[]
  nodeInfoById: NodeMetaMap
}

interface AgentBreakdown {
  nodeId: string
  label: string
  color?: string
  status: 'success' | 'failed' | 'unknown'
  tokens: number
  costUsd: number
  toolCalls: number
  durationMs: number | null
}

/**
 * Compact per-run summary for crews: total agents that fired, cumulative
 * cost, tool-call count, and a per-agent breakdown. Powered entirely by
 * data already sitting on the runs store (agent_usage snapshot the
 * backend emits) so no extra fetch is needed.
 */
export function CrewTimelinePanel({ runs, nodeInfoById }: CrewTimelinePanelProps) {
  const summaries = useMemo(() => {
    return runs.slice(0, 3).map(run => {
      const agents: AgentBreakdown[] = []
      for (const log of run.logs) {
        const output = log.payload?.output as Record<string, unknown> | undefined
        if (!output || typeof output !== 'object') continue
        const usage = output.agent_usage as Record<string, unknown> | undefined
        if (!usage) continue
        const nodeId = log.nodeId ?? 'unknown'
        const info = nodeInfoById.get(nodeId)
        const successMsg = String(output.status ?? '')
        const status: AgentBreakdown['status'] = successMsg === 'success' ? 'success' : successMsg ? 'failed' : 'unknown'
        agents.push({
          nodeId,
          label: info?.label ?? nodeId,
          color: info?.color,
          status,
          tokens: numberOf(usage.total_input_tokens) + numberOf(usage.total_output_tokens),
          costUsd: numberOf(usage.total_cost_usd),
          toolCalls: numberOf(usage.tool_call_count),
          durationMs: numberOf(usage.elapsed_seconds) * 1000 || null,
        })
      }
      const totalCost = agents.reduce((s, a) => s + a.costUsd, 0)
      const totalTokens = agents.reduce((s, a) => s + a.tokens, 0)
      const totalTools = agents.reduce((s, a) => s + a.toolCalls, 0)
      return {
        executionId: run.executionId,
        status: run.status,
        agents,
        totalCost,
        totalTokens,
        totalTools,
      }
    }).filter(s => s.agents.length > 0)
  }, [runs, nodeInfoById])

  if (summaries.length === 0) return null

  return (
    <div className="border-b border-[var(--border-faint)] bg-[var(--bg-2)]">
      {summaries.map(s => (
        <div key={s.executionId} className="px-3 py-2.5">
          <div className="mb-2 flex items-center gap-3 text-[11px]">
            <span className="font-medium uppercase tracking-wider text-[var(--text-mute)]">
              Crew run
            </span>
            <StatChip icon={<Users size={11} />} label={`${s.agents.length} agents`} />
            <StatChip icon={<Coins size={11} />} label={`$${s.totalCost.toFixed(4)}`} />
            <StatChip icon={<Hash size={11} />} label={`${s.totalTokens.toLocaleString()} tokens`} />
            {s.totalTools > 0 && <StatChip label={`${s.totalTools} tool calls`} />}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {s.agents.map((a, i) => (
              <div
                key={`${a.nodeId}-${i}`}
                title={`${a.label} · $${a.costUsd.toFixed(4)} · ${a.tokens} tokens`}
                className="flex items-center gap-1.5 rounded-[6px] border border-[var(--border-faint)] bg-[var(--bg)] px-2 py-1 text-[11px]"
              >
                <span
                  className="h-1.5 w-1.5 rounded-full"
                  style={{
                    background:
                      a.status === 'success'
                        ? 'var(--ok)'
                        : a.status === 'failed'
                          ? 'var(--err)'
                          : a.color || 'var(--text-faint)',
                  }}
                />
                <span className="text-[var(--text)]">{a.label}</span>
                <span className="text-[var(--text-faint)]">
                  ${a.costUsd.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function StatChip({ icon, label }: { icon?: React.ReactNode; label: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-[var(--text-mute)]">
      {icon}
      {label}
    </span>
  )
}

function numberOf(v: unknown): number {
  if (typeof v === 'number' && isFinite(v)) return v
  if (typeof v === 'string') {
    const n = Number(v)
    return isFinite(n) ? n : 0
  }
  return 0
}
