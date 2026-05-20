import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { z } from 'zod'
import { ArrowLeft, CheckCircle2, XCircle, Clock, Loader2, RefreshCw, ChevronDown, ChevronRight, Play } from 'lucide-react'
import { requestJson } from '@/lib/api/client'
import { cn } from '@/lib/utils'

// ── Schemas ──────────────────────────────────────────────────────────────────

const LogSchema = z.object({
  id: z.string(),
  node_id: z.string().nullable().optional(),
  level: z.string(),
  message: z.string(),
  payload: z.any().optional(),
  timestamp: z.string(),
})

const ExecutionDetailSchema = z.object({
  id: z.string(),
  workflow_id: z.string(),
  status: z.string(),
  trigger_type: z.string(),
  input_data: z.any().optional(),
  output_data: z.any().optional(),
  started_at: z.string().nullable().optional(),
  finished_at: z.string().nullable().optional(),
  logs: z.array(LogSchema).default([]),
})

type Log = z.infer<typeof LogSchema>
type ExecutionDetail = z.infer<typeof ExecutionDetailSchema>

// ── Helpers ──────────────────────────────────────────────────────────────────

const STATUS = {
  completed: { icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-400/10', label: 'Completed' },
  failed:    { icon: XCircle,      color: 'text-red-400',   bg: 'bg-red-400/10',   label: 'Failed'    },
  running:   { icon: Loader2,      color: 'text-blue-400',  bg: 'bg-blue-400/10',  label: 'Running'   },
  paused:    { icon: Clock,        color: 'text-yellow-400',bg: 'bg-yellow-400/10',label: 'Paused'    },
}

function formatDuration(start?: string | null, end?: string | null): string {
  if (!start) return '—'
  const s = new Date(start).getTime()
  const e = end ? new Date(end).getTime() : Date.now()
  const ms = e - s
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
}

function formatTs(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 })
}

// ── JSON Collapsible ──────────────────────────────────────────────────────────

const JsonBlock: React.FC<{ data: any; label: string }> = ({ data, label }) => {
  const [open, setOpen] = useState(false)
  if (data == null || (typeof data === 'object' && Object.keys(data).length === 0)) return null
  return (
    <div className="mt-1">
      <button onClick={() => setOpen(v => !v)} className="flex items-center gap-1 text-[11px] text-[var(--text-muted)] hover:text-white transition-colors">
        {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        {label}
      </button>
      {open && (
        <pre className="mt-1.5 p-2.5 bg-[var(--bg-surface-3)] rounded-lg text-[11px] text-[var(--text-muted)] overflow-x-auto leading-relaxed max-h-64">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  )
}

// ── Log entry ─────────────────────────────────────────────────────────────────

const LogEntry: React.FC<{ log: Log }> = ({ log }) => {
  const levelColor = log.level === 'error' ? 'text-red-400' : log.level === 'warning' ? 'text-yellow-400' : 'text-[var(--text-muted)]'
  const payload = log.payload as any

  return (
    <div className={cn('px-4 py-2.5 border-b border-[var(--border-default)] last:border-0', log.level === 'error' && 'bg-red-400/5')}>
      <div className="flex items-start gap-3">
        <span className="text-[10px] text-[var(--text-muted)] font-mono flex-shrink-0 pt-0.5 w-20">{formatTs(log.timestamp)}</span>
        <div className="flex-1 min-w-0">
          <span className={cn('text-[12px] font-medium', levelColor)}>{log.message}</span>
          {payload && (
            <div className="flex gap-4">
              <JsonBlock data={payload?.data_in} label="Input" />
              <JsonBlock data={payload?.output} label="Output" />
              {payload?.error && <JsonBlock data={{ error: payload.error }} label="Error" />}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Node section ──────────────────────────────────────────────────────────────

const NodeSection: React.FC<{ nodeId: string | null; logs: Log[]; nodeNames: Record<string, string> }> = ({ nodeId, logs, nodeNames }) => {
  const [open, setOpen] = useState(true)
  const hasError = logs.some(l => l.level === 'error')
  const label = nodeId ? (nodeNames[nodeId] || nodeId) : 'System'

  return (
    <div className="border border-[var(--border-default)] rounded-xl overflow-hidden mb-3">
      <button
        onClick={() => setOpen(v => !v)}
        className={cn('w-full flex items-center justify-between px-4 py-2.5 bg-[var(--bg-surface-2)] hover:bg-[var(--bg-surface-3)] transition-colors', hasError && 'bg-red-400/10')}
      >
        <div className="flex items-center gap-2.5">
          {hasError
            ? <XCircle className="w-3.5 h-3.5 text-red-400" />
            : <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
          }
          <span className="text-[12px] font-semibold text-white">{label}</span>
          <span className="text-[11px] text-[var(--text-muted)]">{logs.length} log{logs.length !== 1 ? 's' : ''}</span>
        </div>
        {open ? <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" /> : <ChevronRight className="w-4 h-4 text-[var(--text-muted)]" />}
      </button>
      {open && (
        <div className="bg-[var(--bg-surface)]">
          {logs.map(log => <LogEntry key={log.id} log={log} />)}
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export const ExecutionDetailPage: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>()
  const navigate = useNavigate()

  const rerun = useMutation({
    mutationFn: () => requestJson(
      z.object({ execution_id: z.string(), workflow_id: z.string() }),
      { url: `/executions/${executionId}/rerun`, method: 'POST' }
    ),
    onSuccess: (data) => navigate(`/executions/${data.execution_id}`),
  })

  const { data: exec, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['execution', executionId],
    queryFn: () => requestJson(ExecutionDetailSchema, { url: `/executions/${executionId}`, method: 'GET' }),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'running' ? 2000 : false
    },
  })

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-5 h-5 animate-spin text-[var(--text-muted)]" />
      </div>
    )
  }

  if (!exec) {
    return <div className="p-8 text-[var(--text-muted)]">Execution not found</div>
  }

  const s = STATUS[exec.status as keyof typeof STATUS] ?? STATUS.running
  const StatusIcon = s.icon

  // Group logs by node_id
  const groups = new Map<string | null, Log[]>()
  for (const log of exec.logs) {
    const key = log.node_id || null
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(log)
  }

  // Build node name map from logs
  const nodeNames: Record<string, string> = {}
  for (const log of exec.logs) {
    if (log.node_id && log.message && !log.payload) {
      nodeNames[log.node_id] = log.message
    }
  }

  const nodeEntries = Array.from(groups.entries()).filter(([k]) => k !== null) as [string, Log[]][]
  const systemLogs = groups.get(null) || []

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-4xl mx-auto">

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate('/executions')} className="p-1.5 rounded-lg border border-[var(--border-default)] text-[var(--text-muted)] hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="flex-1">
            <div className="flex items-center gap-2.5">
              <div className={cn('flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[12px] font-medium', s.bg, s.color)}>
                <StatusIcon className={cn('w-3.5 h-3.5', exec.status === 'running' && 'animate-spin')} />
                {s.label}
              </div>
              <span className="text-[12px] text-[var(--text-muted)] font-mono">{exec.id.slice(0, 8)}…</span>
            </div>
          </div>
          <div className="flex items-center gap-3 text-[12px] text-[var(--text-muted)]">
            <span>Duration: <span className="text-white font-mono">{formatDuration(exec.started_at, exec.finished_at)}</span></span>
            <span>Trigger: <span className="text-white capitalize">{exec.trigger_type}</span></span>
            <button
              onClick={() => rerun.mutate()}
              disabled={rerun.isPending}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[var(--border-default)] text-[var(--text-muted)] hover:text-white hover:border-indigo-500 transition-colors disabled:opacity-50 text-[12px]"
              title="Re-run with same input"
            >
              {rerun.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Re-run
            </button>
            <button onClick={() => refetch()} className={cn('p-1.5 rounded border border-[var(--border-default)] hover:text-white transition-colors', isFetching && 'opacity-50')}>
              <RefreshCw className={cn('w-3.5 h-3.5', isFetching && 'animate-spin')} />
            </button>
          </div>
        </div>

        {/* Input / Output summary */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {exec.input_data && Object.keys(exec.input_data).length > 0 && (
            <div className="p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)]">
              <p className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wide mb-2">Trigger Input</p>
              <pre className="text-[11px] text-white overflow-x-auto max-h-40">{JSON.stringify(exec.input_data, null, 2)}</pre>
            </div>
          )}
          {exec.output_data && Object.keys(exec.output_data).length > 0 && (
            <div className="p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)]">
              <p className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wide mb-2">Final Output</p>
              <pre className="text-[11px] text-white overflow-x-auto max-h-40">{JSON.stringify(exec.output_data, null, 2)}</pre>
            </div>
          )}
        </div>

        {/* Node logs */}
        <h2 className="text-[13px] font-semibold text-white mb-3">Node Execution</h2>

        {exec.logs.length === 0 ? (
          <p className="text-[13px] text-[var(--text-muted)] italic">No logs recorded for this execution.</p>
        ) : (
          <>
            {nodeEntries.map(([nodeId, logs]) => (
              <NodeSection key={nodeId} nodeId={nodeId} logs={logs} nodeNames={nodeNames} />
            ))}
            {systemLogs.length > 0 && (
              <NodeSection nodeId={null} logs={systemLogs} nodeNames={nodeNames} />
            )}
          </>
        )}
      </div>
    </div>
  )
}
