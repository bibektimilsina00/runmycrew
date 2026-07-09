import { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight, Database } from 'lucide-react'
import type { Run } from '@/features/runs/store/runsStore'

interface MemoryBrowserPanelProps {
  runs: Run[]
}

interface MemoryEntry {
  key: string
  count: number
  messages: unknown[]
  op: string
  nodeId: string | null
}

/**
 * Groups memory-node outputs from the last run by memory_key and shows
 * their latest message list. Powered by the same run-log payloads the
 * CrewTimeline reads, so no extra fetch is needed.
 */
export function MemoryBrowserPanel({ runs }: MemoryBrowserPanelProps) {
  const [expanded, setExpanded] = useState<string | null>(null)

  const entries = useMemo<MemoryEntry[]>(() => {
    const byKey = new Map<string, MemoryEntry>()
    // Read most recent run first so later hits stay (map upsert semantics).
    for (const run of runs.slice(0, 3)) {
      for (const log of run.logs) {
        const output = log.payload?.output as Record<string, unknown> | undefined
        if (!output || typeof output !== 'object') continue
        if (!('messages' in output && 'count' in output)) continue
        // Best effort: use node label as fallback key when the memory-key
        // prop wasn't propagated onto the output shape.
        const key =
          (log.payload?.input as Record<string, unknown> | undefined)?.memory_key as string
          ?? log.nodeId
          ?? 'default'
        const op = String(
          (log.payload?.input as Record<string, unknown> | undefined)?.operation ?? 'get',
        )
        byKey.set(key, {
          key,
          count: Number(output.count) || 0,
          messages: Array.isArray(output.messages) ? output.messages : [],
          op,
          nodeId: log.nodeId ?? null,
        })
      }
    }
    return Array.from(byKey.values())
  }, [runs])

  if (entries.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center">
        <div className="text-[12.5px] text-text-faint">
          <Database size={22} className="mx-auto mb-2 opacity-40" />
          Memory browser lights up once a run touches a Memory node.
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="border-b border-border-faint px-3 py-2 text-[11px] uppercase tracking-wider text-text-mute">
        {entries.length} memory key{entries.length === 1 ? '' : 's'} touched
      </div>
      {entries.map(e => (
        <div key={e.key} className="border-b border-border-faint">
          <button
            className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-[var(--surface)]"
            onClick={() => setExpanded(v => (v === e.key ? null : e.key))}
          >
            {expanded === e.key ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            <span className="flex-1 truncate text-[13px] font-medium text-text">{e.key}</span>
            <span className="text-[11px] text-text-faint">
              {e.count} msg{e.count === 1 ? '' : 's'} · {e.op}
            </span>
          </button>
          {expanded === e.key && (
            <div className="border-t border-border-faint bg-[var(--bg)] px-3 py-2">
              {e.messages.length === 0 ? (
                <p className="text-[11.5px] text-text-faint">empty</p>
              ) : (
                <ol className="flex flex-col gap-1.5">
                  {e.messages.slice(-10).map((m, i) => (
                    <li key={i} className="rounded-[6px] border border-border-faint bg-bg2 p-2">
                      <div className="text-[10.5px] uppercase tracking-wider text-text-faint">
                        {(m as { role?: string }).role ?? 'entry'}
                      </div>
                      <pre className="mt-1 whitespace-pre-wrap break-words font-mono text-[11.5px] text-text">
                        {typeof m === 'string' ? m : JSON.stringify((m as { content?: unknown }).content ?? m, null, 2)}
                      </pre>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
