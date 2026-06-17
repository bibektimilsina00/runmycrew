import { Loader2, Check, AlertTriangle, Wrench, Search, FileText, GitMerge } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { ToolCall } from '../../../../hooks/useCopilotChat'

interface Props {
  calls: ToolCall[]
}

const TOOL_META: Record<string, { label: string; Icon: React.FC<{ className?: string }> }> = {
  search_node_types: { label: 'Searched nodes',   Icon: Search },
  get_node_metadata: { label: 'Read node spec',   Icon: FileText },
  edit_workflow:     { label: 'Edited workflow',  Icon: GitMerge },
}

/**
 * Small horizontal stack of tool-call chips shown above an assistant
 * message. Each chip shows a label inferred from the tool name plus a
 * status indicator (spinner / check / warning).
 */
export function CopilotToolChips({ calls }: Props) {
  if (!calls.length) return null

  return (
    <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
      {calls.map((call, i) => {
        const meta = TOOL_META[call.tool] ?? { label: call.tool, Icon: Wrench }
        return (
          <span
            key={`${call.tool}-${i}`}
            className={cn(
              'inline-flex items-center gap-[6px] rounded-[5px] border px-[8px] py-[3px] text-[11px] font-medium',
              call.status === 'running' && 'border-[var(--border-soft)] bg-[rgba(255,255,255,0.04)] text-[var(--text-mute)]',
              call.status === 'success' && 'border-transparent bg-[var(--badge-ok-bg)] text-[var(--ok)]',
              call.status === 'failed'  && 'border-transparent bg-[var(--badge-err-bg)] text-[var(--err)]',
            )}
            title={call.tool}
          >
            <meta.Icon className="h-3 w-3" />
            <span>{meta.label}</span>
            <StatusIcon status={call.status} />
          </span>
        )
      })}
    </div>
  )
}

function StatusIcon({ status }: { status: ToolCall['status'] }) {
  if (status === 'running') return <Loader2 className="h-3 w-3 animate-spin" />
  if (status === 'success') return <Check className="h-3 w-3" />
  return <AlertTriangle className="h-3 w-3" />
}
